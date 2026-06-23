"""Auth serializers for SusDevOS."""
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

from .models import PasswordResetTokens, RevokedTokens, Users


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            username=data["username"],
            password=data["password"],
        )
        if not user:
            # Try email lookup
            try:
                u = Users.objects.get(email=data["username"])
                if u.check_password(data["password"]):
                    user = u
            except Users.DoesNotExist:
                pass
        if not user:
            # Try username lookup (Users.USERNAME_FIELD is email but username is also unique)
            try:
                u = Users.objects.get(username=data["username"])
                if u.check_password(data["password"]):
                    user = u
            except Users.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError(
                {"code": "invalid_credentials", "detail": "Invalid username or password."}
            )
        if not user.is_active or user.Status == 4:
            raise serializers.ValidationError(
                {"code": "account_disabled", "detail": "This account has been disabled."}
            )
        data["user"] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    entity_id = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = (
            "UserId", "email", "username", "FirstName", "LastName",
            "Designation", "ProfilePicturePath", "IsSuperAdmin",
            "entity_id", "role",
        )

    def get_entity_id(self, obj):
        return obj.EntityId_id

    def get_role(self, obj):
        ur = obj.user_roles.filter(Status=1).select_related("RoleId").first()
        if obj.IsSuperAdmin:
            return "super_admin"
        return ur.RoleId.RoleKey if ur else None


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Return the value regardless — never leak whether email exists
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=10, write_only=True)

    def validate_token(self, value):
        try:
            token = PasswordResetTokens.objects.select_related("UserId").get(Token=value)
        except PasswordResetTokens.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired token.")
        if token.is_used:
            raise serializers.ValidationError("This token has already been used.")
        if token.is_expired:
            raise serializers.ValidationError("This token has expired.")
        self.context["reset_token"] = token
        return value


class OnboardSerializer(serializers.Serializer):
    """First-login password set for newly created users."""
    token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=10, write_only=True)

    def validate_token(self, value):
        try:
            token = PasswordResetTokens.objects.select_related("UserId").get(Token=value)
        except PasswordResetTokens.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        if token.is_used:
            raise serializers.ValidationError("This token has already been used.")
        if token.is_expired:
            raise serializers.ValidationError("This token has expired.")
        self.context["onboard_token"] = token
        return value


# ── User CRUD serializers ──────────────────────────────────────────────────────

class UsersListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ("UserId", "email", "username", "FirstName", "LastName", "EntityId", "role", "Status")

    def get_role(self, obj):
        ur = obj.user_roles.filter(Status=1).select_related("RoleId").first()
        return ur.RoleId.RoleKey if ur else None


class UsersDetailSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    role_id = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = (
            "UserId", "email", "username", "FirstName", "LastName",
            "Designation", "Bio", "PhoneNumber", "ProfilePicturePath",
            "EntityId", "IsSuperAdmin", "is_active", "Status",
            "CreatedAt", "UpdatedAt", "role", "role_id",
        )
        read_only_fields = ("UserId", "email", "EntityId", "IsSuperAdmin", "CreatedAt", "UpdatedAt")

    def get_role(self, obj):
        ur = obj.user_roles.filter(Status=1).select_related("RoleId").first()
        return ur.RoleId.RoleKey if ur else None

    def get_role_id(self, obj):
        ur = obj.user_roles.filter(Status=1).select_related("RoleId").first()
        return ur.RoleId.RoleId if ur else None


class UserCreateSerializer(serializers.ModelSerializer):
    role_key = serializers.CharField(write_only=True)

    class Meta:
        model = Users
        fields = ("email", "username", "FirstName", "LastName", "Designation", "role_key")

    def validate_role_key(self, value):
        from .models import Roles
        allowed = ["admin", "manager", "staff"]
        requesting_user = self.context["request"].user
        if not getattr(requesting_user, "IsSuperAdmin", False):
            if value == "admin" and not requesting_user.user_roles.filter(
                RoleId__RoleKey="admin", Status=1
            ).exists():
                raise serializers.ValidationError("Only Admins can create Admins.")
            if value == "admin" or value == "manager":
                if requesting_user.user_roles.filter(RoleId__RoleKey="staff", Status=1).exists():
                    raise serializers.ValidationError("Staff cannot create Admin or Manager accounts.")
        if value not in allowed and not getattr(requesting_user, "IsSuperAdmin", False):
            raise serializers.ValidationError(f"Invalid role. Choose from: {', '.join(allowed)}")
        return value

    def create(self, validated_data):
        from apps.users.services import invite_user
        role_key  = validated_data.pop("role_key")
        entity_id = self.context["request"].entity_id
        return invite_user(
            entity_id   = entity_id,
            email       = validated_data["email"],
            username    = validated_data.get("username", validated_data["email"].split("@")[0]),
            first_name  = validated_data.get("FirstName", ""),
            last_name   = validated_data.get("LastName", ""),
            designation = validated_data.get("Designation"),
            role_key    = role_key,
        )


class SignupSerializer(serializers.Serializer):
    """
    Self-service registration.
    Creates: Entity → User (Admin role) → EntitySubscription (Free plan).
    Returns the created user; the view issues tokens and logs them in immediately.
    """
    first_name     = serializers.CharField(max_length=100)
    last_name      = serializers.CharField(max_length=100)
    email          = serializers.EmailField()
    company_name   = serializers.CharField(max_length=200)
    password       = serializers.CharField(min_length=10, write_only=True)
    accepted_terms = serializers.BooleanField()

    def validate_email(self, value):
        value = value.lower().strip()
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists. Try signing in."
            )
        return value

    def validate_accepted_terms(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must accept the terms of service to create an account."
            )
        return value

    def create(self, validated_data):
        from apps.users.services import register_new_entity
        return register_new_entity(
            first_name   = validated_data["first_name"],
            last_name    = validated_data["last_name"],
            email        = validated_data["email"],
            company_name = validated_data["company_name"],
            password     = validated_data["password"],
        )


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ("FirstName", "LastName", "Designation", "Bio", "PhoneNumber", "ProfilePicturePath")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=10, write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


# ── RBAC serializers ──────────────────────────────────────────────────────────

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # set at import time
        fields = ("RoleId", "RoleName", "RoleKey", "Description")


class ModulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ("ModuleId", "ModuleName", "ModuleKey", "Description")


class InterfacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ("InterfaceId", "InterfaceName", "InterfaceKey", "ModuleId")


class RolePrivilegesSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ("RolePrivilegeId", "ModuleId", "InterfaceId", "PermissionType")


class PrivilegeOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = ("OverrideId", "InterfaceId", "PermissionType", "OverrideAction")


def _patch_rbac_serializers():
    from .models import (
        Interfaces, Modules, RolePrivileges, Roles, UserPrivilegeOverrides,
    )
    RolesSerializer.Meta.model         = Roles
    ModulesSerializer.Meta.model       = Modules
    InterfacesSerializer.Meta.model    = Interfaces
    RolePrivilegesSerializer.Meta.model = RolePrivileges
    PrivilegeOverrideSerializer.Meta.model = UserPrivilegeOverrides


_patch_rbac_serializers()

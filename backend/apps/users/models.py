"""
Users app models.

Custom user model + full RBAC: Modules -> Interfaces -> Roles -> RolePrivileges
-> UserRoles -> UserPrivilegeOverrides -> DataAccessPrivileges.
Auth tokens: PasswordResetTokens, RevokedTokens.

Schema source: spec/privilege_system_resolved.md (authoritative),
reference migrations 0013_auth_tokens + 0018_user_privilege_overrides.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.entities.models import Entities
from apps.shared.models import BaseAuditMixin


class UsersManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("IsSuperAdmin", True)
        return self.create_user(email, username, password, **extra_fields)


class Users(AbstractBaseUser, PermissionsMixin, BaseAuditMixin):
    """
    Custom user model. Uses email + username for auth.
    EntityId_id links the user to their primary tenant.
    IsSuperAdmin bypasses all privilege checks (SUPERADMIN_BYPASS).
    """

    UserId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(
        Entities, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="users", db_column="EntityId",
    )
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    FirstName = models.CharField(max_length=100, blank=True)
    LastName = models.CharField(max_length=100, blank=True)
    Designation = models.CharField(max_length=200, blank=True)
    Bio = models.TextField(blank=True)
    ProfilePicturePath = models.CharField(max_length=500, blank=True)
    PhoneNumber = models.CharField(max_length=20, blank=True)
    IsSuperAdmin = models.BooleanField(default=False)

    # Django internal fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UsersManager()

    # Map the custom PK so Django's auth machinery works
    @property
    def id(self):
        return self.UserId

    # Used by TenantQueryMiddleware
    @property
    def is_superadmin(self):
        return self.IsSuperAdmin

    class Meta:
        db_table = "users"
        ordering = ["email"]

    def __str__(self):
        return self.email


# -- RBAC ------------------------------------------------------------------

class Modules(BaseAuditMixin):
    """Top-level application area. Seeded via fixture; not user-editable."""

    ModuleId = models.AutoField(primary_key=True)
    ModuleName = models.CharField(max_length=100)
    ModuleKey = models.CharField(max_length=50, unique=True)
    Description = models.TextField(blank=True)

    class Meta:
        db_table = "modules"
        ordering = ["ModuleKey"]

    def __str__(self):
        return self.ModuleName


class Interfaces(BaseAuditMixin):
    """Specific screen or operation within a module. Seeded via fixture."""

    InterfaceId = models.AutoField(primary_key=True)
    ModuleId = models.ForeignKey(Modules, on_delete=models.CASCADE, related_name="interfaces")
    InterfaceName = models.CharField(max_length=100)
    InterfaceKey = models.CharField(max_length=50, unique=True)
    Description = models.TextField(blank=True)

    class Meta:
        db_table = "interfaces"
        ordering = ["InterfaceKey"]

    def __str__(self):
        return self.InterfaceName


class Roles(BaseAuditMixin):
    """Named set of default privileges. Seeded via fixture."""

    ROLE_CHOICES = [
        ("super_admin", "SuperAdmin"),
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("staff", "Staff"),
    ]

    RoleId = models.AutoField(primary_key=True)
    RoleName = models.CharField(max_length=100)
    RoleKey = models.CharField(max_length=20, unique=True, choices=ROLE_CHOICES)
    Description = models.TextField(blank=True)

    class Meta:
        db_table = "roles"
        ordering = ["RoleName"]

    def __str__(self):
        return self.RoleName


class RolePrivileges(BaseAuditMixin):
    """
    Grants a role CRUD access to an interface (or all interfaces in a module
    when InterfaceId is NULL -- the module-level wildcard).
    PermissionType: 1=Create, 2=Read, 3=Update, 4=Delete, 5=All
    """

    PERMISSION_TYPE_CHOICES = [
        (1, "Create"), (2, "Read"), (3, "Update"), (4, "Delete"), (5, "All"),
    ]

    RolePrivilegeId = models.AutoField(primary_key=True)
    RoleId = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="role_privileges")
    ModuleId = models.ForeignKey(Modules, on_delete=models.CASCADE, related_name="role_privileges")
    InterfaceId = models.ForeignKey(
        Interfaces, on_delete=models.CASCADE, null=True, blank=True,
        related_name="role_privileges",
        help_text="NULL = applies to all interfaces in the module",
    )
    PermissionType = models.PositiveSmallIntegerField(choices=PERMISSION_TYPE_CHOICES)

    class Meta:
        db_table = "role_privileges"


class UserRoles(BaseAuditMixin):
    """Assigns a user to a role. A user may hold multiple active roles; privilege
    resolution takes the union of all of them. assign_role currently retires the
    previous role before creating a new one, so single-role remains the norm."""

    UserRoleId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_roles")
    RoleId = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name="user_roles")
    AssignedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_roles"


class UserPrivilegeOverrides(BaseAuditMixin):
    """
    Per-user grant or revoke that overrides the role default.
    OverrideAction: 1=Grant, 2=Revoke
    Ref: 0018_user_privilege_overrides
    """

    PERMISSION_TYPE_CHOICES = [
        (1, "Create"), (2, "Read"), (3, "Update"), (4, "Delete"), (5, "All"),
    ]
    OVERRIDE_ACTION_CHOICES = [(1, "Grant"), (2, "Revoke")]

    OverrideId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="privilege_overrides")
    InterfaceId = models.ForeignKey(Interfaces, on_delete=models.CASCADE, related_name="privilege_overrides")
    PermissionType = models.PositiveSmallIntegerField(choices=PERMISSION_TYPE_CHOICES)
    OverrideAction = models.PositiveSmallIntegerField(choices=OVERRIDE_ACTION_CHOICES)

    class Meta:
        db_table = "user_privilege_overrides"


class DataAccessPrivileges(BaseAuditMixin):
    """Controls which entities' data a user can read, independent of screen access."""

    DataAccessPrivilegeId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="data_access_privileges")
    TargetEntityId = models.ForeignKey(
        Entities, on_delete=models.CASCADE, related_name="data_access_privileges"
    )
    ModuleId = models.ForeignKey(Modules, on_delete=models.CASCADE, related_name="data_access_privileges")
    PermissionType = models.PositiveSmallIntegerField(default=2)  # 2=Read only in v1.0
    Scope = models.PositiveSmallIntegerField(
        default=1, help_text="1=SameHierarchy, 2=CrossHierarchy"
    )
    RecordId = models.IntegerField(null=True, blank=True, help_text="NULL = all records in module")

    class Meta:
        db_table = "data_access_privileges"


# -- Auth tokens -----------------------------------------------------------

class PasswordResetTokens(models.Model):
    """Single-use password reset tokens. Ref: 0013_auth_tokens."""

    TokenId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="password_reset_tokens")
    Token = models.UUIDField(default=uuid.uuid4, unique=True)
    ExpiresAt = models.DateTimeField()
    UsedAt = models.DateTimeField(null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"

    def __str__(self):
        return f"Reset token for {self.UserId} (expires {self.ExpiresAt})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.ExpiresAt

    @property
    def is_used(self):
        return self.UsedAt is not None


class RevokedTokens(models.Model):
    """
    Server-side JWT revocation list. Stores the Jti (JWT ID) of revoked tokens.
    The Celery task purge_expired_revoked_tokens cleans up expired entries.
    Ref: 0013_auth_tokens.
    """

    RevokedTokenId = models.AutoField(primary_key=True)
    Jti = models.UUIDField(unique=True, help_text="JWT 'jti' claim -- unique token identifier")
    UserId = models.ForeignKey(
        Users, on_delete=models.CASCADE, related_name="revoked_tokens"
    )
    RevokedAt = models.DateTimeField(auto_now_add=True)
    ExpiresAt = models.DateTimeField(help_text="When the original token would have expired")

    class Meta:
        db_table = "revoked_tokens"
        indexes = [models.Index(fields=["Jti"], name="idx_revoked_token_jti")]

    def __str__(self):
        return f"Revoked {self.Jti} (user {self.UserId_id})"

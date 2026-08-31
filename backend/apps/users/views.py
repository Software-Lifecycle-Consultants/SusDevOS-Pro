"""
Auth views for SusDevOS.

Endpoints:
  POST /api/auth/login           – email/username + password → access token + HttpOnly refresh cookie
  POST /api/auth/refresh         – refresh cookie → new access token
  POST /api/auth/logout          – revoke refresh token + clear cookie
  POST /api/auth/forgot-password – send password reset email
  POST /api/auth/reset-password  – consume reset token, set new password
  POST /api/auth/onboard         – first-login password set (same mechanism as reset)
  GET  /api/auth/me              – current user profile + full privilege map
"""
import uuid
from datetime import UTC, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.shared.permissions import (
    IsEntityAdmin,
    IsManagerOrAbove,
    build_privilege_map,
)
from apps.shared.views import EntityScopeInitialMixin

from .authentication import clear_refresh_cookie, issue_tokens, set_refresh_cookie
from .models import (
    Interfaces,
    Modules,
    PasswordResetTokens,
    RevokedTokens,
    RolePrivileges,
    Roles,
    UserPrivilegeOverrides,
    UserRoles,
    Users,
)
from .serializers import (
    ForgotPasswordSerializer,
    InterfacesSerializer,
    LoginSerializer,
    ModulesSerializer,
    OnboardSerializer,
    PrivilegeOverrideSerializer,
    ResetPasswordSerializer,
    RolePrivilegesSerializer,
    RolesSerializer,
    SignupSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UsersDetailSerializer,
    UsersListSerializer,
)


class SignupView(APIView):
    """
    POST /api/auth/signup
    Self-service registration: creates Entity + User + Free plan subscription.
    Returns an access token and sets the refresh cookie — user is logged in immediately.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        access, refresh = issue_tokens(user)
        user_data = UserProfileSerializer(user).data

        response = Response(
            {"access_token": access, "user": user_data},
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, refresh)
        return response


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        access, refresh = issue_tokens(user)
        user_data = UserProfileSerializer(user).data

        response = Response(
            {"access_token": access, "user": user_data},
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh)
        return response


class RefreshView(APIView):
    """
    Reads the HttpOnly refresh cookie, validates it (including revocation check),
    and returns a new access token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        raw_refresh = request.COOKIES.get("refresh_token")
        if not raw_refresh:
            return Response(
                {"code": "no_refresh_token", "detail": "Refresh token cookie not found."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            refresh = RefreshToken(raw_refresh)
        except (InvalidToken, TokenError) as e:
            return Response(
                {"code": "invalid_token", "detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check revocation
        jti_str = refresh.get("jti")
        if jti_str:
            try:
                if RevokedTokens.objects.filter(Jti=uuid.UUID(jti_str)).exists():
                    return Response(
                        {"code": "token_revoked", "detail": "Token has been revoked."},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
            except ValueError:
                pass

        # Re-check that the account is still active. The refresh path never loads
        # the user, so without this a deactivated or deleted account (is_active
        # cleared by destroy()/deactivation) could keep minting access tokens for
        # the full 7-day refresh-cookie lifetime — bypassing the login gate.
        user_id = refresh.get(settings.SIMPLE_JWT["USER_ID_CLAIM"])
        user = Users.objects.filter(UserId=user_id).only("is_active").first()
        if user is None or not user.is_active:
            return Response(
                {"code": "account_inactive", "detail": "Account is no longer active."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Revoke the current access token so it's blocked for its remaining lifetime
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            try:
                from rest_framework_simplejwt.tokens import UntypedToken
                raw_access = auth_header.split(" ", 1)[1]
                token = UntypedToken(raw_access)
                jti_str = token.get("jti")
                exp = token.get("exp")
                if jti_str:
                    expires_at = (
                        timezone.datetime.fromtimestamp(exp, tz=UTC)
                        if exp else timezone.now() + timedelta(minutes=15)
                    )
                    RevokedTokens.objects.get_or_create(
                        Jti=uuid.UUID(jti_str),
                        defaults={"UserId": request.user, "ExpiresAt": expires_at},
                    )
            except (InvalidToken, TokenError, ValueError):
                pass

        # Also revoke refresh token if passed in body
        raw_refresh = request.COOKIES.get("refresh_token") or request.data.get("refresh_token")
        if raw_refresh:
            try:
                refresh = RefreshToken(raw_refresh)
                jti_str = refresh.get("jti")
                exp = refresh.get("exp")
                if jti_str:
                    expires_at = (
                        timezone.datetime.fromtimestamp(exp, tz=UTC)
                        if exp else timezone.now() + timedelta(days=7)
                    )
                    RevokedTokens.objects.get_or_create(
                        Jti=uuid.UUID(jti_str),
                        defaults={"UserId": request.user, "ExpiresAt": expires_at},
                    )
            except (InvalidToken, TokenError, ValueError):
                pass

        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = Users.objects.get(email=email, is_active=True)
            token = PasswordResetTokens.objects.create(
                UserId=user,
                ExpiresAt=timezone.now() + timedelta(hours=2),
            )
            reset_url = f"{settings.PASSWORD_RESET_URL}?token={token.Token}"
            send_mail(
                subject="Reset your SusDevOS password",
                message=f"Click the link below to reset your password (valid for 2 hours):\n\n{reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Users.DoesNotExist:
            pass  # Never reveal whether the email exists

        # Always return 204 to prevent email enumeration
        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)
        token = serializer.context["reset_token"]

        user = token.UserId
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        token.UsedAt = timezone.now()
        token.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class OnboardView(APIView):
    """First-login flow for newly invited users — same mechanism as reset password."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OnboardSerializer(data=request.data, context={})
        serializer.is_valid(raise_exception=True)
        token = serializer.context["onboard_token"]

        user = token.UserId
        user.set_password(serializer.validated_data["new_password"])
        user.is_active = True
        user.save()

        token.UsedAt = timezone.now()
        token.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = UserProfileSerializer(user).data
        privileges = build_privilege_map(user)
        return Response({"user": user_data, "privileges": privileges})

    def patch(self, request):
        from .serializers import MeUpdateSerializer
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class MePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        from .serializers import ChangePasswordSerializer
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Users CRUD ────────────────────────────────────────────────────────────────


class UsersViewSet(EntityScopeInitialMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = Users.objects.all()  # overridden by get_queryset; required by DRF router

    # EntityScopeInitialMixin re-resolves request.entity_id AFTER DRF authentication.
    # TenantQueryMiddleware runs before auth, so for JWT requests it leaves entity_id
    # None; without this mixin get_queryset() below would return none() for every
    # non-SuperAdmin (empty user list, 404 on detail) and user creation
    # (UserCreateSerializer.create) would attach EntityId=None (orphan user). Every
    # other tenant-scoped viewset does the same.

    def get_permissions(self):
        """Authorize user-management actions by role.

        Reads (list / retrieve / privileges) stay tenant-scoped IsAuthenticated.
        Inviting a user requires manager-or-above; changing a role, granting or
        removing a privilege override, editing another user, and deactivating a
        user are entity-admin only. This mirrors the entity-admin guards on the
        sibling EntitiesViewSet and closes an in-tenant privilege-escalation path
        (e.g. a staff member self-assigning the admin role via the API, bypassing
        the disabled UI control). SuperAdmin bypasses both classes."""
        admin_only = {
            "assign_role", "add_override", "remove_override",
            "update", "partial_update", "destroy",
        }
        if self.action in admin_only:
            return [IsAuthenticated(), IsEntityAdmin()]
        if self.action == "create":
            return [IsAuthenticated(), IsManagerOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        from .models import Users
        user = self.request.user
        if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return Users.objects.filter(Status__lt=4).select_related("EntityId")
        entity_id = self.request.entity_id
        if not entity_id:
            return Users.objects.none()
        return Users.objects.filter(EntityId_id=entity_id, Status__lt=4).select_related("EntityId")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action == "list":
            return UsersListSerializer
        return UsersDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.Status = 4
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="privileges")
    def privileges(self, request, pk=None):
        from apps.shared.permissions import build_privilege_map
        target_user = self.get_object()
        return Response({
            "user_id": target_user.UserId,
            "role": UsersDetailSerializer(target_user).data.get("role"),
            "privileges": build_privilege_map(target_user),
            "overrides": PrivilegeOverrideSerializer(
                target_user.privilege_overrides.filter(Status=1), many=True
            ).data,
        })

    @action(detail=True, methods=["post"], url_path="privileges/override")
    def add_override(self, request, pk=None):
        target_user = self.get_object()
        serializer = PrivilegeOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        override = UserPrivilegeOverrides.objects.create(
            UserId=target_user,
            **serializer.validated_data,
        )
        return Response(PrivilegeOverrideSerializer(override).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"privileges/override/(?P<override_id>\d+)")
    def remove_override(self, request, pk=None, override_id=None):
        from django.shortcuts import get_object_or_404
        target_user = self.get_object()
        override = get_object_or_404(UserPrivilegeOverrides, OverrideId=override_id, UserId=target_user)
        override.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="role")
    def assign_role(self, request, pk=None):
        """Replace the user's active role."""
        target_user = self.get_object()
        role_key = request.data.get("role_key")
        role = Roles.objects.filter(RoleKey=role_key, Status=1).first()
        if not role:
            return Response({"code": "not_found", "detail": "Role not found."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            UserRoles.objects.filter(UserId=target_user, Status=1).update(Status=4)
            UserRoles.objects.create(UserId=target_user, RoleId=role)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Roles & Modules (read-only) ───────────────────────────────────────────────

class RolesViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Roles.objects.filter(Status=1)
    serializer_class = RolesSerializer
    lookup_field = "RoleId"

    @action(detail=True, methods=["get"], url_path="privileges")
    def role_privileges(self, request, RoleId=None):  # noqa: N803 — URL kwarg name is set by lookup_field
        role = self.get_object()
        privs = RolePrivileges.objects.filter(RoleId=role, Status=1)
        return Response(RolePrivilegesSerializer(privs, many=True).data)


class ModulesViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Modules.objects.filter(Status=1)
    serializer_class = ModulesSerializer
    lookup_field = "ModuleId"

    @action(detail=True, methods=["get"], url_path="interfaces")
    def interfaces(self, request, ModuleId=None):  # noqa: N803 — URL kwarg name is set by lookup_field
        module = self.get_object()
        ifaces = Interfaces.objects.filter(ModuleId=module, Status=1)
        return Response(InterfacesSerializer(ifaces, many=True).data)

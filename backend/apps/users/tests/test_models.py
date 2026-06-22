import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.users.models import (
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
from apps.users.tests.factories import (
    InterfacesFactory,
    ModulesFactory,
    RolesFactory,
    SuperAdminFactory,
    UserPrivilegeOverridesFactory,
    UserRolesFactory,
    UsersFactory,
)


@pytest.mark.django_db
class TestUsers:
    def test_create_user(self):
        user = UsersFactory(email="test@example.com")
        assert user.pk is not None
        assert user.email == "test@example.com"
        assert user.IsSuperAdmin is False

    def test_password_is_hashed(self):
        user = UsersFactory()
        assert not user.password.startswith("testpassword")
        assert user.check_password("testpassword123!")

    def test_superadmin_flag(self):
        sa = SuperAdminFactory()
        assert sa.IsSuperAdmin is True
        assert sa.is_superadmin is True  # property used by middleware

    def test_entity_id_property_via_middleware_attr(self):
        user = UsersFactory()
        # TenantQueryMiddleware reads user.EntityId_id
        assert user.EntityId_id == user.EntityId.EntityId

    def test_str(self):
        user = UsersFactory(email="alice@example.com")
        assert str(user) == "alice@example.com"

    def test_audit_defaults(self):
        user = UsersFactory()
        assert user.Status == 1
        assert user.CreatedAt is not None


@pytest.mark.django_db
class TestRBAC:
    def test_module_interface_relation(self):
        module = ModulesFactory(ModuleKey="emissions")
        iface = InterfacesFactory(ModuleId=module, InterfaceKey="verify_emissions")
        assert iface.ModuleId_id == module.ModuleId

    def test_role_privilege_module_wildcard(self):
        """InterfaceId=None means all interfaces in the module."""
        role = RolesFactory()
        module = ModulesFactory()
        priv = RolePrivileges.objects.create(
            RoleId=role, ModuleId=module, InterfaceId=None, PermissionType=5
        )
        assert priv.InterfaceId_id is None

    def test_user_role_assignment(self):
        user = UsersFactory()
        role = RolesFactory(RoleKey="admin", RoleName="Admin")
        ur = UserRolesFactory(UserId=user, RoleId=role)
        assert user.user_roles.filter(Status=1).count() == 1
        assert ur.RoleId.RoleKey == "admin"

    def test_privilege_override_grant(self):
        override = UserPrivilegeOverridesFactory(OverrideAction=1)
        assert override.OverrideAction == 1  # Grant

    def test_privilege_override_revoke(self):
        override = UserPrivilegeOverridesFactory(OverrideAction=2)
        assert override.OverrideAction == 2  # Revoke


@pytest.mark.django_db
class TestAuthTokens:
    def test_password_reset_token_not_expired(self):
        user = UsersFactory()
        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() + timedelta(hours=1),
        )
        assert not token.is_expired
        assert not token.is_used

    def test_password_reset_token_expired(self):
        user = UsersFactory()
        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() - timedelta(seconds=1),
        )
        assert token.is_expired

    def test_revoked_token_unique_jti(self):
        user = UsersFactory()
        jti = uuid.uuid4()
        RevokedTokens.objects.create(
            Jti=jti, UserId=user, ExpiresAt=timezone.now() + timedelta(days=1)
        )
        from django.db import IntegrityError, transaction
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                RevokedTokens.objects.create(
                    Jti=jti, UserId=user, ExpiresAt=timezone.now() + timedelta(days=1)
                )

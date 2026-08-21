"""
Authorization + tenant-resolution tests for UsersViewSet (user management).

Regression coverage for audit finding U1:

  1. Post-auth entity resolution is restored (UsersViewSet now inherits
     EntityScopeInitialMixin). Before the fix, TenantQueryMiddleware left
     request.entity_id = None for JWT requests, so get_queryset() returned
     none() for every non-SuperAdmin — an entity admin saw an empty user list
     and "Invite user" created a tenant-less orphan account.

  2. Privileged actions are role-gated. assign_role / privilege-override /
     create / destroy were previously reachable by any authenticated tenant
     member, which — once (1) is fixed — would let a staff user self-assign the
     admin role via a direct API call (the UI control is only client-side).
"""
from rest_framework import status
from rest_framework.test import APIClient

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.shared.permissions import _resolve_privilege
from apps.users.models import (
    Interfaces,
    Modules,
    Roles,
    UserPrivilegeOverrides,
    UserRoles,
    Users,
)
from apps.users.tests.factories import (
    RolePrivilegesFactory,
    UserRolesFactory,
    UsersFactory,
)


def _client(user, entity):
    """APIClient authenticated as `user` with the X-Entity-ID header set."""
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(entity.EntityId),
    )
    return client


def _role(key):
    role, _ = Roles.objects.get_or_create(RoleKey=key, defaults={"RoleName": key.title()})
    return role


@pytest.fixture
def staff_user(db, entity):
    user = UsersFactory(EntityId=entity, email="staff@testcorp.com", username="teststaff")
    UserRoles.objects.create(UserId=user, RoleId=_role("staff"))
    return user


@pytest.fixture
def manager_user(db, entity):
    user = UsersFactory(EntityId=entity, email="manager@testcorp.com", username="testmgr")
    UserRoles.objects.create(UserId=user, RoleId=_role("manager"))
    return user


@pytest.mark.django_db
class TestUsersViewSetAuthorization:
    """A staff member must not be able to escalate privilege or manage accounts."""

    def test_staff_cannot_self_assign_admin_role(self, entity, staff_user):
        _role("admin")  # the target role must exist for a meaningful test
        resp = _client(staff_user, entity).patch(
            f"/api/users/{staff_user.UserId}/role/",
            {"role_key": "admin"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        # The role must be unchanged — no escalation.
        assert not staff_user.user_roles.filter(RoleId__RoleKey="admin", Status=1).exists()

    def test_staff_cannot_grant_privilege_override(self, entity, staff_user):
        module = Modules.objects.create(ModuleName="Emissions", ModuleKey="emissions")
        iface = Interfaces.objects.create(
            ModuleId=module, InterfaceName="Verify", InterfaceKey="verify_emissions",
        )
        resp = _client(staff_user, entity).post(
            f"/api/users/{staff_user.UserId}/privileges/override/",
            {"InterfaceId": iface.InterfaceId, "PermissionType": 5, "OverrideAction": 1},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert UserPrivilegeOverrides.objects.filter(UserId=staff_user).count() == 0

    def test_staff_cannot_remove_privilege_override(self, entity, staff_user):
        # A pre-existing Revoke override limiting the staff member: removing it
        # would be an escalation, so the DELETE action must be admin-only too.
        module = Modules.objects.create(ModuleName="Reports", ModuleKey="reports")
        iface = Interfaces.objects.create(
            ModuleId=module, InterfaceName="Export", InterfaceKey="export_reports",
        )
        override = UserPrivilegeOverrides.objects.create(
            UserId=staff_user, InterfaceId=iface, PermissionType=2, OverrideAction=2,
        )
        resp = _client(staff_user, entity).delete(
            f"/api/users/{staff_user.UserId}/privileges/override/{override.OverrideId}/",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert UserPrivilegeOverrides.objects.filter(OverrideId=override.OverrideId).exists()

    def test_staff_cannot_invite_user(self, entity, staff_user):
        resp = _client(staff_user, entity).post(
            "/api/users/",
            {
                "email": "new@testcorp.com", "username": "newbie",
                "FirstName": "New", "LastName": "Hire", "role_key": "staff",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert not Users.objects.filter(email="new@testcorp.com").exists()

    def test_staff_cannot_deactivate_user(self, entity, staff_user):
        target = UsersFactory(EntityId=entity, email="victim@testcorp.com", username="victim")
        resp = _client(staff_user, entity).delete(f"/api/users/{target.UserId}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        target.refresh_from_db()
        assert target.is_active is True
        assert target.Status != 4


@pytest.mark.django_db
class TestUsersViewSetEntityResolution:
    """The management feature must actually work for an entity admin/manager."""

    def test_admin_lists_own_tenant_users(self, entity, admin_user, staff_user):
        # Before the fix this returned an empty page (request.entity_id was None).
        resp = _client(admin_user, entity).get("/api/users/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {row["UserId"] for row in resp.data["results"]}
        assert admin_user.UserId in ids
        assert staff_user.UserId in ids

    def test_admin_can_change_role(self, entity, admin_user, staff_user):
        _role("manager")
        resp = _client(admin_user, entity).patch(
            f"/api/users/{staff_user.UserId}/role/",
            {"role_key": "manager"},
            format="json",
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert staff_user.user_roles.filter(RoleId__RoleKey="manager", Status=1).exists()

    def test_manager_can_invite_user_into_tenant(self, entity, manager_user):
        _role("staff")  # so the invited user is actually assigned the role
        resp = _client(manager_user, entity).post(
            "/api/users/",
            {
                "email": "invitee@testcorp.com", "username": "invitee",
                "FirstName": "In", "LastName": "Vitee", "role_key": "staff",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        created = Users.objects.get(email="invitee@testcorp.com")
        # Entity resolution restored → the invitee is attached to the tenant,
        # not created as an orphan with EntityId = None.
        assert created.EntityId_id == entity.EntityId
        assert created.user_roles.filter(RoleId__RoleKey="staff", Status=1).exists()


@pytest.mark.django_db
class TestResolvePrivilegeMultiRole:
    """_resolve_privilege must union privileges across every active role (F2).

    UserRoles has no unique_together and no Meta.ordering, so a user with two
    active roles previously had their privileges resolved off an arbitrary
    .first() row instead of the union of both roles.
    """

    def test_two_active_roles_union_their_privileges(self, entity):
        module = Modules.objects.create(ModuleName="Emissions", ModuleKey="emissions_multi")
        iface_a = Interfaces.objects.create(
            ModuleId=module, InterfaceName="View A", InterfaceKey="view_a_multi",
        )
        iface_b = Interfaces.objects.create(
            ModuleId=module, InterfaceName="View B", InterfaceKey="view_b_multi",
        )

        role_manager = _role("manager")
        role_staff = _role("staff")
        RolePrivilegesFactory(
            RoleId=role_manager, ModuleId=module, InterfaceId=iface_a, PermissionType=2,
        )
        RolePrivilegesFactory(
            RoleId=role_staff, ModuleId=module, InterfaceId=iface_b, PermissionType=2,
        )

        user = UsersFactory(EntityId=entity, email="multirole@testcorp.com", username="multirole")
        UserRolesFactory(UserId=user, RoleId=role_manager)
        UserRolesFactory(UserId=user, RoleId=role_staff)

        # Before the fix, exactly one of these would fail depending on which
        # UserRoles row .first() happened to return.
        assert _resolve_privilege(user, "view_a_multi", 2) is True
        assert _resolve_privilege(user, "view_b_multi", 2) is True

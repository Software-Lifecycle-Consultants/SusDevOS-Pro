"""
DRF permission classes for SusDevOS.

Resolution order (from spec/privilege_system_resolved.md):
  1. SuperAdmin → bypass everything  # SUPERADMIN_BYPASS
  2. UserPrivilegeOverrides (Revoke wins over Grant at same level)
  3. Role-based RolePrivileges (via UserRoles)

Usage in views:
    permission_classes = [IsAuthenticated, HasModulePrivilege("view_emissions", 2)]
"""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "IsSuperAdmin", False))


class IsEntityAdmin(BasePermission):
    """User has the 'admin' role within their entity."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return True
        return request.user.user_roles.filter(
            RoleId__RoleKey="admin", Status=1
        ).exists()


class IsManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if getattr(request.user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return True
        return request.user.user_roles.filter(
            RoleId__RoleKey__in=["admin", "manager"], Status=1
        ).exists()


class HasModulePrivilege(BasePermission):
    """
    Checks the full privilege resolution chain for a specific interface + permission type.
    Instantiate with: permission_classes = [HasModulePrivilege("create_emissions", 1)]
    """

    def __init__(self, interface_key: str, permission_type: int):
        self.interface_key = interface_key
        self.permission_type = permission_type

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
            return True
        return _resolve_privilege(user, self.interface_key, self.permission_type)


def _resolve_privilege(user, interface_key: str, permission_type: int) -> bool:
    """
    Returns True if the user has the requested permission on the interface.
    Implements the algorithm from spec/privilege_system_resolved.md.
    """
    from apps.users.models import Interfaces, RolePrivileges, UserPrivilegeOverrides, UserRoles

    try:
        interface = Interfaces.objects.select_related("ModuleId").get(
            InterfaceKey=interface_key, Status=1
        )
    except Interfaces.DoesNotExist:
        return False

    # 1. User-specific overrides (Revoke beats Grant at same level)
    override = UserPrivilegeOverrides.objects.filter(
        UserId=user,
        InterfaceId=interface,
        PermissionType__in=[permission_type, 5],  # 5 = All
        Status=1,
    ).order_by("-OverrideAction").first()  # 2=Revoke first (desc) → Revoke wins over Grant
    if override:
        # If any active override is Revoke → deny; if Grant → allow
        return override.OverrideAction == 1

    # 2. Role-based privileges
    user_role = UserRoles.objects.filter(UserId=user, Status=1).select_related("RoleId").first()
    if not user_role:
        return False

    return RolePrivileges.objects.filter(
        RoleId=user_role.RoleId,
        ModuleId=interface.ModuleId,
        InterfaceId__in=[interface, None],  # None = module-level wildcard
        PermissionType__in=[permission_type, 5],
        Status=1,
    ).exists()


def build_privilege_map(user) -> dict:
    """
    Returns a flat {interface_key: bool} map of all interfaces for the given user.
    Used by GET /auth/me to populate the frontend Zustand store.
    """
    from apps.users.models import Interfaces

    if getattr(user, "IsSuperAdmin", False):  # SUPERADMIN_BYPASS
        return {
            iface.InterfaceKey: True
            for iface in Interfaces.objects.filter(Status=1)
        }

    interfaces = Interfaces.objects.filter(Status=1).select_related("ModuleId")
    return {
        iface.InterfaceKey: _resolve_privilege(user, iface.InterfaceKey, 2)  # 2=Read as baseline
        for iface in interfaces
    }

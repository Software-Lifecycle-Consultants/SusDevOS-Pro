from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    DataAccessPrivileges,
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


@admin.register(Users)
class UsersAdmin(BaseUserAdmin):
    list_display = ("UserId", "email", "username", "IsSuperAdmin", "is_active", "Status")
    list_filter = ("IsSuperAdmin", "is_active", "Status")
    search_fields = ("email", "username", "FirstName", "LastName")
    ordering = ("email",)
    readonly_fields = ("CreatedAt", "UpdatedAt")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Personal", {"fields": ("FirstName", "LastName", "Designation", "Bio", "PhoneNumber")}),
        ("Entity", {"fields": ("EntityId",)}),
        ("Permissions", {"fields": ("IsSuperAdmin", "is_active", "is_staff", "is_superuser")}),
        ("Audit", {"fields": ("Status", "CreatedAt", "UpdatedAt")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "username", "password1", "password2")}),
        ("Entity", {"fields": ("EntityId",)}),
    )


@admin.register(Modules)
class ModulesAdmin(admin.ModelAdmin):
    list_display = ("ModuleId", "ModuleName", "ModuleKey", "Status")
    search_fields = ("ModuleName", "ModuleKey")


@admin.register(Interfaces)
class InterfacesAdmin(admin.ModelAdmin):
    list_display = ("InterfaceId", "InterfaceName", "InterfaceKey", "ModuleId", "Status")
    list_filter = ("ModuleId",)
    search_fields = ("InterfaceName", "InterfaceKey")


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ("RoleId", "RoleName", "RoleKey", "Status")


@admin.register(RolePrivileges)
class RolePrivilegesAdmin(admin.ModelAdmin):
    list_display = ("RolePrivilegeId", "RoleId", "ModuleId", "InterfaceId", "PermissionType")
    list_filter = ("RoleId", "PermissionType")


@admin.register(UserRoles)
class UserRolesAdmin(admin.ModelAdmin):
    list_display = ("UserRoleId", "UserId", "RoleId", "AssignedAt", "Status")
    list_filter = ("RoleId",)
    search_fields = ("UserId__email",)


@admin.register(UserPrivilegeOverrides)
class UserPrivilegeOverridesAdmin(admin.ModelAdmin):
    list_display = ("OverrideId", "UserId", "InterfaceId", "PermissionType", "OverrideAction")
    list_filter = ("OverrideAction", "PermissionType")


admin.site.register(DataAccessPrivileges)
admin.site.register(PasswordResetTokens)
admin.site.register(RevokedTokens)

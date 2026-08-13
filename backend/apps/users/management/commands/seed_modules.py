"""
Management command: seed_modules

Seeds Modules, Interfaces, Roles, and the default RolePrivileges from
apps/users/fixtures/modules.yml.

Safe to run multiple times — uses get_or_create throughout.

Usage:
    python manage.py seed_modules
"""
import os

from django.core.management.base import BaseCommand

import yaml

# Default role privilege matrix — mirrors spec/privilege_system_resolved.md
# Format: (role_key, module_key, interface_key_or_None, permission_type)
# permission_type: 1=Create, 2=Read, 3=Update, 4=Delete, 5=All
# interface_key=None means the privilege applies to ALL interfaces in that module
ROLE_PRIVILEGES = [
    # ── SuperAdmin: everything (module-level wildcards) ────────────────────────
    # (SuperAdmin bypasses checks in code, but seeding here for completeness)
    ("super_admin", "entity_management", None, 5),
    ("super_admin", "user_management",   None, 5),
    ("super_admin", "projects",          None, 5),
    ("super_admin", "land_parcels",      None, 5),
    ("super_admin", "ecosystem",         None, 5),
    ("super_admin", "tree_removals",     None, 5),
    ("super_admin", "restorations",      None, 5),
    ("super_admin", "emissions",         None, 5),
    ("super_admin", "reports",           None, 5),
    ("super_admin", "blog",              None, 5),
    ("super_admin", "notifications",     None, 5),
    ("super_admin", "audit",             None, 5),
    ("super_admin", "settings",          None, 5),

    # ── Admin: full CRUD on everything within their entity ────────────────────
    ("admin", "entity_management", None, 5),
    ("admin", "user_management",   None, 5),
    ("admin", "projects",          None, 5),
    ("admin", "land_parcels",      None, 5),
    ("admin", "ecosystem",         None, 5),
    ("admin", "tree_removals",     None, 5),
    ("admin", "restorations",      None, 5),
    ("admin", "emissions",         None, 5),
    ("admin", "reports",           None, 5),
    ("admin", "blog",              None, 5),
    ("admin", "notifications",     None, 2),  # Read only
    ("admin", "audit",             None, 2),  # Read only
    ("admin", "settings",          None, 5),

    # ── Manager: no entity mgmt write, no audit, no verify/unlock ─────────────
    ("manager", "entity_management", "view_entities",      2),
    ("manager", "user_management",   "view_users",         2),
    ("manager", "user_management",   "create_user",        1),
    ("manager", "projects",          None,                 5),
    ("manager", "land_parcels",      None,                 5),
    ("manager", "ecosystem",         None,                 5),
    ("manager", "tree_removals",     None,                 5),
    ("manager", "restorations",      None,                 5),
    ("manager", "emissions",         "view_emissions",     2),
    ("manager", "emissions",         "create_emissions",   1),
    ("manager", "emissions",         "edit_emissions",     3),
    ("manager", "emissions",         "delete_emissions",   4),
    ("manager", "emissions",         "import_emissions",   1),
    ("manager", "reports",           None,                 5),
    ("manager", "blog",              "view_blog",          2),
    ("manager", "notifications",     None,                 2),
    ("manager", "settings",          "view_settings",      2),

    # ── Staff: domain data CRUD, no user mgmt write, read-only reports/blog ───
    ("staff", "user_management",  "view_users",        2),
    ("staff", "projects",         None,                5),
    ("staff", "land_parcels",     None,                5),
    ("staff", "ecosystem",        None,                5),
    ("staff", "tree_removals",    None,                5),
    ("staff", "restorations",     None,                5),
    ("staff", "emissions",        "view_emissions",    2),
    ("staff", "emissions",        "create_emissions",  1),
    ("staff", "emissions",        "edit_emissions",    3),
    ("staff", "emissions",        "delete_emissions",  4),
    ("staff", "reports",          "view_reports",      2),
    ("staff", "blog",             "view_blog",         2),
    ("staff", "notifications",    None,                2),
]


class Command(BaseCommand):
    help = "Seed Modules, Interfaces, Roles, and default RolePrivileges from fixtures/modules.yml"

    def handle(self, *args, **options):
        from apps.users.models import Interfaces, Modules, RolePrivileges, Roles

        fixture_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "fixtures", "modules.yml",
        )
        with open(fixture_path) as f:
            data = yaml.safe_load(f)

        # ── Modules & Interfaces ───────────────────────────────────────────────
        module_map = {}
        for mod_data in data.get("modules", []):
            module, created = Modules.objects.get_or_create(
                ModuleKey=mod_data["key"],
                defaults={"ModuleName": mod_data["name"]},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created module: {mod_data['key']}"))
            module_map[mod_data["key"]] = module

            for iface_data in mod_data.get("interfaces", []):
                iface, created = Interfaces.objects.get_or_create(
                    InterfaceKey=iface_data["key"],
                    defaults={"ModuleId": module, "InterfaceName": iface_data["name"]},
                )
                if created:
                    self.stdout.write(f"    Created interface: {iface_data['key']}")

        # ── Roles ─────────────────────────────────────────────────────────────
        role_map = {}
        for role_data in data.get("roles", []):
            role, created = Roles.objects.get_or_create(
                RoleKey=role_data["key"],
                defaults={
                    "RoleName":    role_data["name"],
                    "Description": role_data.get("description", ""),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  Created role: {role_data['key']}"))
            role_map[role_data["key"]] = role

        # ── RolePrivileges ─────────────────────────────────────────────────────
        created_count = 0
        for role_key, module_key, interface_key, perm_type in ROLE_PRIVILEGES:
            role   = role_map.get(role_key)
            module = module_map.get(module_key)
            if not role or not module:
                self.stderr.write(f"  Skipping unknown role/module: {role_key}/{module_key}")
                continue

            iface = None
            if interface_key:
                try:
                    iface = Interfaces.objects.get(InterfaceKey=interface_key)
                except Interfaces.DoesNotExist:
                    self.stderr.write(f"  Interface not found: {interface_key}")
                    continue

            _, created = RolePrivileges.objects.get_or_create(
                RoleId=role,
                ModuleId=module,
                InterfaceId=iface,
                PermissionType=perm_type,
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_count} new RolePrivilege rows created."
        ))

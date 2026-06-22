# SusDevOS — Privilege System (Resolved)

## Decision

**Use the Modules → Interfaces → RolePrivileges pattern** from the migration files.  
**Retire** the Features/PrivilegeID/wildcard notation from the Enhanced Privilege System Design doc.

The migration-based pattern is already partially implemented and maps directly to the UI ("module-interface" terminology matches the product spec). The Enhanced Privilege doc was a design exploration; this document supersedes it.

---

## Core Concepts

**Module** — A top-level area of the application (e.g. Entity Management, User Management, Projects, Emissions, Reports). Seeded via fixture; not editable at runtime.

**Interface** — A specific screen or operation within a module (e.g. "Create Project", "Verify Emissions Record", "Generate Report"). Seeded via fixture; not editable at runtime.

**Role** — A named set of default privileges (SuperAdmin, Admin, Manager, Staff). Seeded via fixture.

**RolePrivilege** — A record granting a role CRUD access to a specific interface (or all interfaces in a module).

**UserRole** — Assigns a user to exactly one role per v1.0.

**UserPrivilegeOverride** — A per-user grant or revoke that overrides the role default. Allows exceptions without creating new roles.

**DataAccessPrivilege** — Controls which *entities' data* a user can read, separate from what *screens* they can access.

---

## Database Schema

### Modules (seeded)
```
ModuleId      INT PK
ModuleName    VARCHAR(100)   — e.g. "Entity Management"
ModuleKey     VARCHAR(50)    — e.g. "entity_management" (used in code)
Description   TEXT
+ BaseAuditMixin
```

### Interfaces (seeded)
```
InterfaceId   INT PK
ModuleId      FK → Modules
InterfaceName VARCHAR(100)   — e.g. "Create Entity"
InterfaceKey  VARCHAR(50)    — e.g. "create_entity" (used in code)
Description   TEXT
+ BaseAuditMixin
```

### Roles (seeded)
```
RoleId        INT PK
RoleName      VARCHAR(100)   — SuperAdmin | Admin | Manager | Staff
RoleKey       VARCHAR(20)    — super_admin | admin | manager | staff
Description   TEXT
+ BaseAuditMixin
```

### RolePrivileges (seeded)
```
RolePrivilegeId  INT PK
RoleId           FK → Roles
ModuleId         FK → Modules
InterfaceId      FK → Interfaces  NULL = applies to ALL interfaces in the module (wildcard)
PermissionType   TINYINT          1=Create, 2=Read, 3=Update, 4=Delete, 5=All
+ BaseAuditMixin
```

When `InterfaceId IS NULL`, the privilege applies to every interface within that module — this replaces the `x-*` wildcard notation from the original design doc.

### UserRoles
```
UserRoleId    INT PK
UserId        FK → Users
RoleId        FK → Roles
AssignedAt    DATETIME
+ BaseAuditMixin
```

Constraint: A user may only have one active UserRole record at a time (enforced at application layer in v1.0).

### UserPrivilegeOverrides (new — replaces User Overrides Table from original doc)
```
OverrideId       INT PK
UserId           FK → Users
InterfaceId      FK → Interfaces
PermissionType   TINYINT          1=Create, 2=Read, 3=Update, 4=Delete, 5=All
OverrideAction   TINYINT          1=Grant, 2=Revoke
+ BaseAuditMixin
```

### DataAccessPrivileges (unchanged from migrations)
```
DataAccessPrivilegeId  INT PK
UserId                 FK → Users
TargetEntityId         FK → Entities
ModuleId               FK → Modules
PermissionType         TINYINT   1=Read (only Read in v1.0)
Scope                  TINYINT   1=SameHierarchy, 2=CrossHierarchy
RecordId               INT NULL  — NULL = applies to all records in module
+ BaseAuditMixin
```

---

## Privilege Resolution Algorithm

```python
def get_effective_privileges(user_id: int, interface_key: str, permission_type: int) -> bool:
    """
    Returns True if the user has the requested permission on the interface.
    Resolution order:
      1. UserPrivilegeOverrides (Revoke wins over Grant at same level)
      2. Role-based RolePrivileges (via UserRoles)
    SuperAdmins bypass all checks — handled before calling this function.
    """
    user = Users.objects.get(pk=user_id)
    interface = Interfaces.objects.get(InterfaceKey=interface_key)

    # 1. Check user-specific overrides for this interface
    override = UserPrivilegeOverrides.objects.filter(
        UserId=user_id,
        InterfaceId=interface.InterfaceId,
        PermissionType__in=[permission_type, 5],  # 5=All
    ).first()

    if override:
        return override.OverrideAction == 1  # 1=Grant, 2=Revoke

    # 2. Fall back to role-based privileges
    user_role = UserRoles.objects.filter(UserId=user_id, Status=1).first()
    if not user_role:
        return False

    return RolePrivileges.objects.filter(
        RoleId=user_role.RoleId,
        ModuleId=interface.ModuleId,
        InterfaceId__in=[interface.InterfaceId, None],  # None = module-level wildcard
        PermissionType__in=[permission_type, 5],
        Status=1,
    ).exists()
```

---

## Default Role Privilege Matrix

### SuperAdmin
- Bypass flag: all permission checks return True.
- Can access all modules, all entities, all records.
- `# SUPERADMIN_BYPASS` comment required in code wherever this bypass is applied.

### Admin
| Module | Interfaces | Permissions |
|--------|-----------|-------------|
| Entity Management | All | CRUD |
| User Management | All | CRUD (own entity + related branches) |
| Projects | All | CRUD |
| Land Parcels | All | CRUD |
| Ecosystem | All | CRUD |
| Species | All | CRUD |
| Tree Removals | All | CRUD |
| Restorations | All | CRUD |
| Emissions | All | CRUD + Verify |
| Reports | All | Create, Read |
| Blog | All | CRUD |
| Notifications | All | Read |
| Audit Logs | Read | Read (own entity) |
| Settings | All | CRUD |

### Manager
| Module | Interfaces | Permissions |
|--------|-----------|-------------|
| Entity Management | View only | Read |
| User Management | Create Staff | Create, Read |
| Projects | All | CRUD |
| Land Parcels | All | CRUD |
| Ecosystem | All | CRUD |
| Species | All | CRUD |
| Tree Removals | All | CRUD |
| Restorations | All | CRUD |
| Emissions | All | CRUD (cannot Verify) |
| Reports | All | Create, Read |
| Blog | View only | Read |
| Notifications | All | Read |
| Audit Logs | — | None |
| Settings | View only | Read |

### Staff
| Module | Interfaces | Permissions |
|--------|-----------|-------------|
| Entity Management | — | None |
| User Management | View only (own entity users) | Read |
| Projects | All | CRUD |
| Land Parcels | All | CRUD |
| Ecosystem | All | CRUD |
| Species | All | CRUD |
| Tree Removals | All | CRUD |
| Restorations | All | CRUD |
| Emissions | All | CRUD (cannot Verify) |
| Reports | View only | Read |
| Blog | View only | Read |
| Notifications | All | Read |
| Audit Logs | — | None |
| Settings | — | None |

---

## Modules & Interfaces Fixture (apps/users/fixtures/modules.yml)

```yaml
modules:
  - key: entity_management
    name: Entity Management
    interfaces:
      - key: view_entities
        name: View Entities
      - key: create_entity
        name: Create Entity
      - key: edit_entity
        name: Edit Entity
      - key: delete_entity
        name: Delete Entity (Soft)
      - key: manage_entity_api_keys
        name: Manage API Keys

  - key: user_management
    name: User Management
    interfaces:
      - key: view_users
        name: View Users
      - key: create_user
        name: Create User
      - key: edit_user
        name: Edit User
      - key: delete_user
        name: Delete User (Soft)
      - key: manage_privileges
        name: Manage User Privileges

  - key: projects
    name: Development Projects
    interfaces:
      - key: view_projects
        name: View Projects
      - key: create_project
        name: Create Project
      - key: edit_project
        name: Edit Project
      - key: delete_project
        name: Delete Project
      - key: manage_phases
        name: Manage Phases

  - key: land_parcels
    name: Land Parcels
    interfaces:
      - key: view_land_parcels
        name: View Land Parcels
      - key: create_land_parcel
        name: Create Land Parcel
      - key: edit_land_parcel
        name: Edit Land Parcel
      - key: delete_land_parcel
        name: Delete Land Parcel

  - key: ecosystem
    name: Ecosystem & Species
    interfaces:
      - key: view_ecosystem
        name: View Ecosystem
      - key: create_ecosystem
        name: Create Ecosystem
      - key: edit_ecosystem
        name: Edit Ecosystem
      - key: view_species
        name: View Species
      - key: create_species
        name: Create Species
      - key: edit_species
        name: Edit Species

  - key: tree_removals
    name: Tree Removals
    interfaces:
      - key: view_tree_removals
        name: View Tree Removals
      - key: create_tree_removal
        name: Create Tree Removal
      - key: edit_tree_removal
        name: Edit Tree Removal
      - key: delete_tree_removal
        name: Delete Tree Removal

  - key: restorations
    name: Restorations
    interfaces:
      - key: view_restorations
        name: View Restorations
      - key: create_restoration
        name: Create Restoration
      - key: edit_restoration
        name: Edit Restoration
      - key: delete_restoration
        name: Delete Restoration

  - key: emissions
    name: Emissions
    interfaces:
      - key: view_emissions
        name: View Emissions Records
      - key: create_emissions
        name: Create Emissions Record
      - key: edit_emissions
        name: Edit Emissions Record
      - key: delete_emissions
        name: Delete Emissions Record
      - key: verify_emissions
        name: Verify Emissions Record
      - key: unlock_emissions
        name: Unlock Verified Record (SuperAdmin)
      - key: import_emissions
        name: Bulk Import Emissions

  - key: reports
    name: Reports
    interfaces:
      - key: view_reports
        name: View Reports
      - key: generate_report
        name: Generate Report

  - key: blog
    name: Blog
    interfaces:
      - key: view_blog
        name: View Blog (CMS)
      - key: create_blog_post
        name: Create Blog Post
      - key: edit_blog_post
        name: Edit Blog Post
      - key: publish_blog_post
        name: Publish Blog Post

  - key: notifications
    name: Notifications
    interfaces:
      - key: view_notifications
        name: View Notifications

  - key: audit
    name: Audit Logs
    interfaces:
      - key: view_audit_logs
        name: View Audit Logs

  - key: settings
    name: Settings
    interfaces:
      - key: view_settings
        name: View Settings
      - key: edit_settings
        name: Edit Settings
```

---

## Frontend Integration

The `/api/v1/auth/me` endpoint returns the user's complete effective privilege set as a flat list of interface keys with permitted actions:

```json
{
  "user": { "id": 1, "username": "achala", "role": "admin" },
  "privileges": {
    "view_projects": true,
    "create_project": true,
    "edit_project": true,
    "delete_project": true,
    "verify_emissions": true,
    "unlock_emissions": false
  }
}
```

The React frontend stores this in Zustand at login. Component-level access checks use a `usePrivilege(interfaceKey)` hook. Table action columns (Edit, Delete) render conditionally based on this hook — no server round-trip needed per row.

```typescript
// hooks/usePrivilege.ts
export const usePrivilege = (interfaceKey: string): boolean => {
  const privileges = usePrivilegeStore(state => state.privileges)
  return privileges[interfaceKey] ?? false
}

// Usage in a component
const canDelete = usePrivilege('delete_project')
```

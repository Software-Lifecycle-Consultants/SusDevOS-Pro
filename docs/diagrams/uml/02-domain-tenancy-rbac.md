# 02 — Tenancy & RBAC Domain Model

The multi-tenancy root (`Entities`) and the privilege system that governs every request.


**Related user stories** — [Tenancy & access — SDO-TEN-01…16](../../stories/01-tenancy-access.md)

## Tenancy

```mermaid
classDiagram
    direction TB

    class Entities {
        +EntityId: AutoField PK
        +EntityName: Char
        +EntityType: SmallInt «1..8»
        +ConsolidationApproach: SmallInt «1..3»
        +ParentEntityId: FK self, PROTECT
        +Status: SmallInt
    }

    class RelatedEntities {
        <<junction>>
        +ParentEntityId: FK
        +ChildEntityId: FK
        +RelationshipType
    }

    class EntityMembers {
        +UserId: FK CASCADE
        +EntityId: FK CASCADE
        +CreatedBy / CreatedAt
        %% grants multi-entity access
    }

    class Users {
        +UserId: PK
        +EntityId: FK PROTECT «primary/home entity»
        +username / email
        +IsSuperAdmin: bool
        +Designation
    }

    class EntityLocations { <<junction>> }
    class EntityContacts { <<junction>> }
    class EntityDocuments { <<junction>> }
    class EntityTags { <<junction>> }
    class EntityApiKeysIntermediary { <<junction>> }

    Entities "1" --> "*" Entities : ParentEntityId (self-hierarchy)
    Entities "1" --> "*" RelatedEntities : peer graph
    Entities "1" --> "*" Users : home entity
    Entities "1" --> "*" EntityMembers
    Users "1" --> "*" EntityMembers : additional entities
    Entities "1" --> "*" EntityLocations
    Entities "1" --> "*" EntityContacts
    Entities "1" --> "*" EntityDocuments
    Entities "1" --> "*" EntityTags
    Entities "1" --> "*" EntityApiKeysIntermediary
```

A user has exactly one **home** entity (`Users.EntityId`) and zero or more **additional**
entities via `EntityMembers`. That is what makes an ESG consultant serving several clients
possible without duplicating the user.

## RBAC — Modules → Interfaces → RolePrivileges

```mermaid
classDiagram
    direction LR

    class Modules {
        +ModuleId: PK
        +ModuleKey
        +ModuleName
        +Status
    }

    class Interfaces {
        +InterfaceId: PK
        +ModuleId: FK CASCADE
        +InterfaceKey «unique lookup key»
        +Status
    }

    class Roles {
        +RoleId: PK
        +RoleName
        +Status
    }

    class RolePrivileges {
        +RoleId: FK CASCADE
        +ModuleId: FK CASCADE
        +InterfaceId: FK nullable «null = module wildcard»
        +PermissionType: SmallInt «5 = All»
        +Status
    }

    class UserRoles {
        +UserId: FK CASCADE
        +RoleId: FK CASCADE
        +Status
    }

    class UserPrivilegeOverrides {
        +UserId: FK CASCADE
        +InterfaceId: FK CASCADE
        +PermissionType «5 = All»
        +OverrideAction: 1=Grant, 2=Revoke
        +Status
    }

    class DataAccessPrivileges {
        +UserId: FK CASCADE
        +TargetEntityId: FK
        +ModuleId: FK CASCADE
    }

    class Users

    Modules "1" --> "*" Interfaces
    Roles "1" --> "*" RolePrivileges
    Modules "1" --> "*" RolePrivileges
    Interfaces "1" --> "*" RolePrivileges
    Users "1" --> "*" UserRoles
    Roles "1" --> "*" UserRoles
    Users "1" --> "*" UserPrivilegeOverrides
    Interfaces "1" --> "*" UserPrivilegeOverrides
    Users "1" --> "*" DataAccessPrivileges
    Modules "1" --> "*" DataAccessPrivileges
```

### Privilege resolution algorithm

Implemented in `_resolve_privilege()`. The order is significant — overrides short-circuit
roles entirely, and a Revoke beats a Grant at the same level.

```mermaid
flowchart TD
    START(["_resolve_privilege(user, interface_key, permission_type)"]) --> LOOKUP["Look up Interfaces<br/>by InterfaceKey, Status=1"]
    LOOKUP -->|"not found"| DENY1["return False"]
    LOOKUP --> OVR["Query UserPrivilegeOverrides<br/>PermissionType in (requested, 5=All)<br/>order_by −OverrideAction"]
    OVR -->|"override exists"| ORACT{"OverrideAction<br/>== 1 (Grant)?"}
    ORACT -->|"Yes"| ALLOW1["return True"]
    ORACT -->|"No (2=Revoke)"| DENY2["return False"]
    OVR -->|"no override"| ROLE["✅ F2 — union of all active UserRoles<br/>RoleId__in across every active role"]
    ROLE -->|"none"| DENY3["return False"]
    ROLE --> RP["RolePrivileges match?<br/>RoleId + ModuleId<br/>+ InterfaceId in (interface, NULL)<br/>+ PermissionType in (requested, 5)"]
    RP -->|"exists"| ALLOW2["return True"]
    RP -->|"none"| DENY4["return False"]

    style ALLOW1 fill:#e8f5e9,stroke:#1b5e20,color:#000
    style ALLOW2 fill:#e8f5e9,stroke:#1b5e20,color:#000
    style DENY1 fill:#ffebee,stroke:#b71c1c,color:#000
    style DENY2 fill:#ffebee,stroke:#b71c1c,color:#000
    style DENY3 fill:#ffebee,stroke:#b71c1c,color:#000
    style DENY4 fill:#ffebee,stroke:#b71c1c,color:#000
    style ROLE fill:#e8f5e9,stroke:#1b5e20,color:#000
```

**`ORDER BY -OverrideAction` is load-bearing.** `2` (Revoke) sorts before `1` (Grant), so a
Revoke wins when both exist. The `.first()` depends on that ordering — this is correct, but
it is not obvious, and removing the ordering would silently invert the precedence.

> **✅ F2 · Authorization — union across active roles — fixed 2026-08-21.**
> `apps/shared/permissions.py:89` used to read `UserRoles.objects.filter(...).first()` with
> **no `order_by`**. `UserRoles` is a many-to-many table, so a user could hold several active
> roles, but privileges were not the union of them — one arbitrary role won, and a user granted
> both `Manager` and a narrow custom role could silently lose their Manager privileges, with the
> effective role able to change after a table rewrite with no data change at all.
> **Now:** `_resolve_privilege` unions across every active role (`RoleId__in=role_ids`),
> matching what `IsEntityAdmin`/`IsManagerOrAbove` already did. No `UniqueConstraint` was added
> — deliberately, since the union makes multi-role well-defined and such a migration could fail
> against pre-existing duplicate rows. `assign_role` now runs inside `transaction.atomic()` so
> its retire-then-create pair cannot interleave.
> See [F2 in the findings register](../FINDINGS.md#f2).

`build_privilege_map()` returns a flat `{interface_key: bool}` for `GET /auth/me`, which
populates the frontend Zustand store. SuperAdmin bypasses the whole algorithm.

## Token & credential models

```mermaid
classDiagram
    class Users
    class RevokedTokens {
        +Jti: UUID «server-side revocation»
        +UserId: FK
        +ExpiresAt
    }
    class PasswordResetTokens {
        +UserId: FK CASCADE
        +Token
        +ExpiresAt
        +UsedAt
    }
    class EntityApiKeys {
        +ApiKeyId: PK
        +HashedApiKey / KeyPrefix
        +TargetEntityId
        +ExpiryDate
    }

    Users "1" --> "*" RevokedTokens
    Users "1" --> "*" PasswordResetTokens
```

Access tokens are 15-minute JWTs held in memory; the 7-day refresh token is an HttpOnly
cookie scoped to `Path=/api/auth/refresh`. Logout writes the `Jti` into `RevokedTokens`,
which `RevokedTokenJWTAuthentication` checks on every request — so revocation is immediate
rather than waiting for expiry.

---
*Source: `backend/apps/entities/models.py`, `backend/apps/users/models.py`,
`backend/apps/shared/permissions.py`, `backend/apps/users/authentication.py`*

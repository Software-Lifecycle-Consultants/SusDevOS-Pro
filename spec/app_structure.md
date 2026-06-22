# SusDevOS — Django App Structure

## Project Layout

```
susdevos/                        # repo root
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── susdevos/                    # Django project package
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py                  # root URL conf — mounts /api/v1/ and /api/public/
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── core/                    # Shared abstractions — no models of its own
│   ├── entities/
│   ├── users/
│   ├── projects/
│   ├── land/
│   ├── ecosystem/
│   ├── emissions/
│   ├── restorations/
│   ├── shared/
│   ├── notifications/
│   ├── blog/
│   ├── reports/
│   └── audit/
└── tests/
    ├── conftest.py
    ├── factories/
    └── e2e/
```

## App Breakdown

### `apps/core`
No migrations. Houses:
- `models.py` — `BaseAuditMixin` abstract model (Status, ApprovalStatus, DeletedAt, CreatedAt, UpdatedAt, CreatedBy, UpdatedBy)
- `managers.py` — `TenantManager` (injects EntityId filter on every queryset via middleware)
- `middleware.py` — `TenantQueryMiddleware` (reads request.user.entity_id, sets on thread-local)
- `permissions.py` — DRF base permission classes (`IsSuperAdmin`, `IsEntityAdmin`, `IsManager`, `IsStaff`, `HasModulePrivilege`)
- `pagination.py` — Cursor-based pagination class
- `serializers.py` — Base serializer with audit field read-only handling
- `exceptions.py` — Custom DRF exception handler mapping to standard error envelope
- `storage.py` — S3/MinIO backend wrapper (pre-signed URL generation)
- `tasks.py` — Shared Celery tasks (S3 cleanup, log retention purge)

```python
# core/models.py
class BaseAuditMixin(models.Model):
    Status = models.PositiveSmallIntegerField(
        default=1,
        help_text="1: Active, 2: Disabled, 3: Draft, 4: Deleted"
    )
    ApprovalStatus = models.PositiveSmallIntegerField(
        default=1,
        help_text="1: Active, 2: Rejected, 3: Pending"
    )
    DeletedAt = models.DateTimeField(null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.IntegerField(null=True, blank=True)
    UpdatedBy = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True
```

---

### `apps/entities`
**Models:** `Entities`, `RelatedEntities`
**Junction tables:** `EntityLocations`, `EntityContacts`, `EntityDocuments`, `EntityTags`, `EntityApiKeysIntermediary`
**Depends on:** `apps.shared` (Locations, Contacts, Documents, Tags, EntityApiKeys)

---

### `apps/users`
**Models:** `Users`, `Roles`, `Modules`, `Interfaces`, `UserRoles`, `RolePrivileges`, `UserPrivilegeOverrides`, `DataAccessPrivileges`, `PasswordResetTokens`, `RevokedTokens`
**Depends on:** `apps.entities`

Note: `Modules` and `Interfaces` live here because they define the privilege surface for user roles. They are seeded via a data migration — not user-created at runtime.

---

### `apps/projects`
**Models:** `DevelopmentProjects`, `RelatedProjects`, `ProjectPhases`
**Junction tables:** `DevelopmentProjectTags`, `DevelopmentProjectPartners`, `DevelopmentProjectLandParcels`, `DevelopmentProjectContacts`, `DevelopmentProjectDocuments`, `DevelopmentProjectImages`, `DevelopmentProjectEntities`
**Depends on:** `apps.entities`, `apps.shared`, `apps.land` (LandParcels FK)

---

### `apps/land`
**Models:** `LandParcels`
**Junction tables:** `LandParcelTags`, `LandParcelEcosystems`, `LandParcelContacts`, `LandParcelDocuments`, `LandParcelImages`, `LandParcelEntities`, `LandParcelLocations`
**Depends on:** `apps.entities`, `apps.shared`, `apps.ecosystem`

---

### `apps/ecosystem`
**Models:** `Ecosystem`, `Species`
**Junction tables:** `EcosystemTags`, `SpeciesTags`, `SpeciesLandParcels`
**Depends on:** `apps.shared`

Note: `SpeciesLandParcels` uses a raw `IntegerField` for `LandParcelId` to avoid a circular dependency with `apps.land`. Referential integrity enforced at application layer.

---

### `apps/emissions`
**Models:** `GwpDatasets`, `GwpValues`, `EmissionsData`, `EmissionsDetails`, `EmissionsOffsets`
**Depends on:** `apps.entities`, `apps.projects`

This app owns all GHG calculation logic. The `EmissionsData.save()` override triggers server-side calculation. No client-computed values are trusted.

---

### `apps/restorations`
**Models:** `TreeRemovals`, `Restorations`
**Junction tables:** `TreeRemovalEcosystems`, `TreeRemovalTags`, `TreeRemovalContacts`, `TreeRemovalDocuments`, `TreeRemovalLandParcels`, `TreeRemovalEntities`, `TreeRemovalImages`, `TreeRemovalLocationIds`, `TreeRemovalRemovedSpecies`, `TreeRemovalAffectedSpecies`, `RestorationEcosystems`, `RestorationTags`, `RestorationDevelopmentProjects`, `RestorationEntities`, `RestorationSpecies`, `RestorationLandParcels`, `RestorationLocations`, `RestorationContacts`, `RestorationDocuments`, `RestorationImages`
**Depends on:** `apps.entities`, `apps.shared`, `apps.ecosystem`, `apps.projects`

---

### `apps/shared`
**Models:** `Locations`, `Contacts`, `Documents`, `Images`, `Tags`, `EntityApiKeys`
**Depends on:** nothing (base app — no FK dependencies on other apps)

All shared lookup/attachment models. Locations are global (not entity-scoped). All others are entity-scoped.

---

### `apps/notifications`
**Models:** `Notifications`
**Depends on:** `apps.entities`, `apps.users`

---

### `apps/blog`
**Models:** `Blogs`
**Depends on:** `apps.entities`, `apps.users`

Public endpoint `/api/public/blog/{slug}/` requires no authentication. All other blog endpoints require Admin role.

---

### `apps/reports`
**Models:** `ReportJobs`
**Depends on:** `apps.entities`, `apps.projects`, `apps.emissions`

Report generation is async via Celery. A `ReportJob` record tracks status (Queued → Processing → Complete → Failed). The download URL is a pre-signed S3 URL valid for 24 hours.

---

### `apps/audit`
**Models:** `AuditLog`
**Depends on:** `apps.entities`, `apps.users`

Populated exclusively via Django signals and a shared `audit_log()` helper — never written to directly from business logic.

---

## INSTALLED_APPS Order

```python
INSTALLED_APPS = [
    # Django
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "storages",
    "corsheaders",
    "django_celery_beat",
    # Project core
    "apps.core",
    # Project apps
    "apps.shared",
    "apps.entities",
    "apps.users",
    "apps.ecosystem",
    "apps.land",
    "apps.projects",
    "apps.emissions",
    "apps.restorations",
    "apps.notifications",
    "apps.blog",
    "apps.reports",
    "apps.audit",
]
```

## Migration Dependency Chain

```
apps.shared (0001)
    └── apps.entities (0001)
        └── apps.users (0001)
            └── apps.ecosystem (0001)
                └── apps.land (0001)
                    └── apps.projects (0001)
                        └── apps.emissions (0001)
                            └── apps.restorations (0001)
                                └── apps.notifications (0001)
                                └── apps.blog (0001)
                                └── apps.reports (0001)
                                └── apps.audit (0001)
```

## URL Structure

```
/api/v1/auth/         → users.urls (login, logout, refresh, forgot-password, reset-password, onboarding)
/api/v1/entities/     → entities.urls
/api/v1/users/        → users.urls
/api/v1/roles/        → users.urls
/api/v1/modules/      → users.urls
/api/v1/projects/     → projects.urls
/api/v1/land-parcels/ → land.urls
/api/v1/ecosystems/   → ecosystem.urls
/api/v1/species/      → ecosystem.urls
/api/v1/tree-removals/→ restorations.urls
/api/v1/restorations/ → restorations.urls
/api/v1/emissions/    → emissions.urls
/api/v1/gwp-datasets/ → emissions.urls
/api/v1/reports/      → reports.urls
/api/v1/notifications/→ notifications.urls
/api/v1/blog/         → blog.urls (authenticated CMS)
/api/v1/audit-logs/   → audit.urls
/api/v1/settings/     → entities.urls
/api/v1/files/        → shared.urls (pre-signed URL generation)
/api/public/blog/     → blog.urls (unauthenticated public)
```

## Seeding / Bootstrap

A `management/commands/seed_superadmins.py` command in `apps/users` creates the two hardcoded SuperAdmin records. This must be run once on first deployment. SuperAdmin credentials are read from environment variables (`SUPERADMIN_1_EMAIL`, `SUPERADMIN_1_PASSWORD`, `SUPERADMIN_2_EMAIL`, `SUPERADMIN_2_PASSWORD`).

A separate `seed_modules.py` command seeds all `Modules` and `Interfaces` rows from a static YAML fixture (`apps/users/fixtures/modules.yml`). These rows define the privilege surface and must exist before any roles can be configured.

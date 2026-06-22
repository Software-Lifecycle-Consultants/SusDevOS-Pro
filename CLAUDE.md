# SusDevOS — Claude Context

## What this project is

SusDevOS is a multi-tenant SaaS platform for sustainable development tracking:
- **GHG emissions** (Scope 1/2/3, GHG Protocol Corporate Standard)
- **Ecosystem tracking** (tree removals, restorations, IPCC LULUCF biomass carbon)
- **SBTi target tracking**, CDP export, TNFD-aligned reporting

Target users: sustainability managers, ESG consultants, development project managers.

## Spec documents — read before building anything

All design decisions are documented in `spec/`. Read the relevant spec before implementing:

| File | Covers |
|------|--------|
| `spec/app_structure.md` | 12 Django apps, model list per app, dependency order, migration chain |
| `spec/endpoint_catalog.md` | ~100 REST endpoints, request/response shapes, auth requirements |
| `spec/privilege_system_resolved.md` | RBAC: Modules → Interfaces → RolePrivileges. **Use this, not Features/PrivilegeID doc** |
| `spec/ghg_calculation_spec.md` | All GHG formulas, unit conversion pipeline, IPCC biomass, Scope 2 dual method |
| `spec/api_integrations.md` | Climatiq, Companies House, Verra, ECB FX, GBIF, SBTi, DEFRA integrations |
| `spec/celery_tasks.md` | All Celery tasks, schedules, retry policies, queue routing |
| `spec/pricing.md` | Feature gate matrix, FeatureGateMixin, plan tiers |
| `spec/compliance.md` | GDPR, Cyber Essentials, ISO 27001 roadmap, audit log retention |

## Tech stack

**Backend:** Django 5.1 + DRF + PostgreSQL/PostGIS + Celery/Redis + S3/MinIO
**Frontend:** Next.js 14 (App Router) + TypeScript + shadcn/ui + Tailwind + TanStack Query + Zustand
**API contract:** drf-spectacular (OpenAPI 3) → orval (TypeScript client generation)

## Key architecture decisions

**Multi-tenancy:** Single-database, row-level scoping via `TenantQueryMiddleware` (sets `request.entity_id`). All querysets MUST filter by `EntityId`. Never trust `EntityId` from request body — always use `request.entity_id`.

**Auth:** JWT (15-min access token) + 7-day HttpOnly refresh cookie. Server-side revocation via `RevokedTokens` table (Jti UUID). No client-side token storage.

**Calculations:** All GHG calculations are server-side only. `EmissionsData.save()` override triggers calculation. Client-submitted `EmissionsAmount` values are overwritten. See `spec/ghg_calculation_spec.md` §13.

**Feature gates:** `FeatureGateMixin` on views checks `PlanFeatures` table. Returns `{"code": "feature_gated", "feature": "...", "upgrade_url": "/pricing"}` which the frontend renders as an upgrade modal.

**Migrations:** Numbered 0010–0028 in `backend/migrations/`. Each app's own migrations live in `apps/{app}/migrations/`. The numbered series in `backend/migrations/` are design-phase reference migrations — actual Django migrations belong in each app.

## App load order (INSTALLED_APPS)

`shared` → `entities` → `users` → `projects` → `land` → `ecosystem` → `emissions` → `restorations` → `notifications` → `blog` → `reports` → `billing`

## Critical rules

1. **Never compute emissions on the client.** `EmissionsAmount` is always server-populated.
2. **Never skip `request.entity_id` filtering.** Every queryset involving tenant data needs `.filter(EntityId=request.entity_id)`.
3. **Verified inventories are immutable.** `GHGInventories.VerificationStatus >= 3` → reject edits with HTTP 403.
4. **Biogenic CO2 is NOT in the GWP total.** It goes in `BiogenicCO2AmountTonnes` and is reported separately.
5. **Scope 2 requires both methods.** Always compute both `EmissionsAmountLocationBased` and `EmissionsAmountMarketBased`.
6. **Feature gates are server-enforced.** Never rely on frontend-only gating.

## Running locally

```bash
# 1. Start infrastructure
docker compose up db redis minio -d

# 2. Set up backend
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 3. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Environment

- Python 3.12
- Node 20 LTS
- PostgreSQL 16 with PostGIS 3.4
- Redis 7

## Where things live

```
backend/
  config/          Django project config (settings, urls, celery, wsgi)
  apps/            12 Django apps
  migrations/      Design-phase numbered migrations (0010–0028) — reference only
  tasks/           Celery task modules
spec/              All design and architecture documentation
frontend/
  src/app/         Next.js App Router pages
  src/components/  Shared UI components (shadcn/ui)
  src/lib/         API client (orval-generated) and utilities
  src/hooks/       TanStack Query hooks
  src/store/       Zustand stores
```

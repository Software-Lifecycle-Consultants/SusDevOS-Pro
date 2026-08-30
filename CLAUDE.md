# SusDevOS — Claude Context

## What this project is

SusDevOS is a multi-tenant SaaS platform for sustainable development tracking:
- **GHG emissions** (Scope 1/2/3, GHG Protocol Corporate Standard)
- **Ecosystem tracking** (tree removals, restorations, IPCC LULUCF biomass carbon)
- **Verra/Gold Standard MRV**, TNFD-aligned biodiversity reporting

Target users: sustainability managers, ESG consultants, development project managers.

## Product scope — IN and OUT (authoritative)

The product was refocused on **nature / MRV + TNFD** (commit "remove SBTi, CDP, NDC, RE100").
This list is the source of truth — if a spec/marketing doc still describes an OUT-of-scope
feature, the doc is stale, not a backlog item.

**In scope:** GHG accounting (Scope 1/2/3, GHG Protocol; market- & location-based Scope 2),
IPCC LULUCF biomass carbon (tree removals + restoration sequestration), TNFD-aligned
biodiversity (Species + GBIF/IUCN), carbon-credit MRV (Verra / Gold Standard validation),
emission factors via Climatiq (aggregator), generic Targets/milestones, reporting (CSV/PDF).

**Out of scope — do NOT (re)build:**
- **SBTi** — no target-validation/registry sync, no SBTi-specific tiers or marketing.
- **CDP** — no CDP export format / questionnaire mapping / Partner Program integration.
- **NDC** — no "counts toward NDC" tagging (field removed).
- **RE100** — no renewable-electricity commitment tracking.
- **Customer/developer API access (temporary, until PMF)** — no customer-managed API keys,
  public API documentation, API tier entitlements, or third-party programmatic access. The
  first-party browser REST API and local OpenAPI → Orval development tooling remain in scope.

Generic GHG capabilities that happen to *support* external frameworks (e.g. market-based
Scope 2) stay in scope — just don't frame or build them as SBTi/CDP/NDC/RE100 features.

## Spec documents — read before building anything

All design decisions are documented in `spec/`. Read the relevant spec before implementing:

| File | Covers |
|------|--------|
| `spec/app_structure.md` | 12 Django apps, model list per app, dependency order, migration chain |
| `spec/endpoint_catalog.md` | ~100 REST endpoints, request/response shapes, auth requirements |
| `spec/privilege_system_resolved.md` | RBAC: Modules → Interfaces → RolePrivileges. **Use this, not Features/PrivilegeID doc** |
| `spec/ghg_calculation_spec.md` | All GHG formulas, unit conversion pipeline, IPCC biomass, Scope 2 dual method |
| `spec/api_integrations.md` | Climatiq, Companies House, Verra, ECB FX, GBIF, DEFRA integrations |
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

**Feature gates — currently OFF.** Plans are sold on **service and hosting tiers** (seats, entities, reporting years, support level), not on which capabilities unlock, so every authenticated tenant gets the full feature set. `settings.FEATURE_GATES_ENABLED` (default `False`) short-circuits `FeatureGateMixin` and `is_feature_enabled()`.

The machinery is kept, not deleted: with the switch on, `FeatureGateMixin` checks `PlanFeatures` and returns HTTP 402 Payment Required with `{"code": "feature_gated", "feature": "...", "detail": "...", "upgrade_url": "/pricing"}`, which the frontend renders as an upgrade modal. Tests cover both states, so gating can be reintroduced by flipping the flag.

**Plan limits are unaffected by the switch** — `MaxEntities`, `MaxUsersPerEntity`, `MaxReportingYears` and `MaxApiCallsPerDay` resolve through `get_active_plan()`, not `is_feature_enabled()`.

**But no plan limit is enforced today.** `can_add_entity()` and `record_api_call()` exist in `apps/billing/services.py` with **no callers**; `MaxUsersPerEntity` and `MaxReportingYears` are stored and seeded but never compared. Wiring these up is outstanding work, not something the gate switch removed.

**Migrations:** Numbered 0010–0028 in `backend/migrations/`. Each app's own migrations live in `apps/{app}/migrations/`. The numbered series in `backend/migrations/` are design-phase reference migrations — actual Django migrations belong in each app.

## App load order (INSTALLED_APPS)

`shared` → `entities` → `users` → `projects` → `land` → `ecosystem` → `emissions` → `restorations` → `notifications` → `blog` → `reports` → `billing`

## Critical rules

1. **Never compute emissions on the client.** `EmissionsAmount` is always server-populated.
2. **Never skip `request.entity_id` filtering.** Every queryset involving tenant data needs `.filter(EntityId=request.entity_id)`.
3. **Verified inventories are immutable.** `GHGInventories.VerificationStatus >= 3` → reject edits with HTTP 403.
4. **Biogenic CO2 is NOT in the GWP total.** It goes in `BiogenicCO2AmountTonnes` and is reported separately.
5. **Scope 2 requires both methods.** Always compute both `EmissionsAmountLocationBased` and `EmissionsAmountMarketBased`.
6. **Do not add new per-capability feature gates.** Packaging is by service and hosting tier. If gating ever returns, it is server-enforced — never frontend-only — via `FeatureGateMixin`, which is kept but switched off.

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

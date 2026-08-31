export interface DiagramDef {
  id: string;
  tab: string;
  level: string;
  title: string;
  description: string;
  chart: string;
}

export const DIAGRAMS: DiagramDef[] = [
  {
    id: "l1",
    tab: "Context",
    level: "Level 1",
    title: "System Context",
    description:
      "Who uses SusDevOS, and which external systems does it depend on? Four user personas interact with the platform; seven external services are integrated.",
    chart: `C4Context
    title System Context — SusDevOS

    Person(sm, "Sustainability Manager", "Enters and manages GHG emissions data, closes GHG inventories, tracks targets and milestones, and views reports.")
    Person(esg, "ESG Consultant", "Accesses multiple client entities from one login. Validates data quality. Exports CSV and PDF reports.")
    Person(pm, "Project Manager", "Tracks development project carbon footprint, land parcel activities, and ecosystem restoration MRV.")
    Person(sysadmin, "Platform Admin", "Super-admin access. Manages all tenants, users, and billing plans.")

    System(susdevos, "SusDevOS", "Multi-tenant SaaS platform for GHG accounting (Scope 1/2/3, GHG Protocol), nature and ecosystem tracking (TNFD-aligned), carbon-credit MRV (Verra/Gold Standard), and sustainability reporting.")

    System_Ext(climatiq, "Climatiq", "Emission factor aggregator. Synced weekly to populate the in-platform factor library.")
    System_Ext(verra, "Verra VCS Registry", "Carbon credit serial lookup and validation for Verified Carbon Standard offsets.")
    System_Ext(gs, "Gold Standard Registry", "Carbon credit serial lookup and validation for Gold Standard offsets.")
    System_Ext(ecb, "ECB / OER", "Daily EUR reference rates (ECB, 17:00 CET) and Open Exchange Rates fallback for multi-currency cost accounting.")
    System_Ext(gbif, "GBIF + IUCN", "Species occurrence records (GBIF) and Red List conservation status (IUCN) for biodiversity tracking.")
    System_Ext(ch, "Companies House", "UK company record lookup used during entity onboarding and validation.")
    System_Ext(smtp, "SMTP / Amazon SES", "Transactional email for report delivery, verification alerts, and system notifications.")

    Rel(sm, susdevos, "Enters activity data, manages inventories, views reports", "HTTPS")
    Rel(esg, susdevos, "Manages multiple client entities, validates data quality", "HTTPS")
    Rel(pm, susdevos, "Tracks project footprint and restoration carbon sequestration", "HTTPS")
    Rel(sysadmin, susdevos, "Manages platform tenants, users, and billing plans", "HTTPS")

    Rel(susdevos, climatiq, "Syncs emission factors weekly (Sunday 02:00 UTC)", "HTTPS REST")
    Rel(susdevos, verra, "Validates VCS credit serials daily (03:00 UTC)", "HTTPS REST")
    Rel(susdevos, gs, "Validates Gold Standard serials daily (03:30 UTC)", "HTTPS REST")
    Rel(susdevos, ecb, "Fetches daily FX rates (17:00 UTC)", "HTTPS REST")
    Rel(susdevos, gbif, "Fetches species occurrence data on demand", "HTTPS REST")
    Rel(susdevos, ch, "Validates UK company records on entity creation", "HTTPS REST")
    Rel(susdevos, smtp, "Sends notifications, report links, verification alerts", "SMTP / HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="2")`,
  },
  {
    id: "l2",
    tab: "Containers",
    level: "Level 2",
    title: "Container Diagram",
    description:
      "What deployable units make up the platform, and how do they communicate? Shows Nginx, Next.js SPA, Django API, three Celery worker pools, Beat scheduler, PostgreSQL, Redis, and Cloudflare R2.",
    chart: `C4Container
    title Container Diagram — SusDevOS Platform (Contabo VPS)

    Person(user, "Platform User", "Sustainability manager, ESG consultant, project manager, or platform admin")

    System_Boundary(platform, "SusDevOS Platform") {
        Container(nginx, "Reverse Proxy", "Nginx", "TLS termination via Let's Encrypt. Routes /* to Next.js, /api/* to Gunicorn. Serves and caches static assets.")
        Container(spa, "Web Application", "Next.js 14 / TypeScript / shadcn/ui", "App Router SPA. TanStack Query for server state. Zustand auth store (JWT in memory only). orval-generated TypeScript REST client from OpenAPI spec.")
        Container(api, "REST API", "Python 3.12 / Django 5.1 / DRF / Gunicorn", "JWT auth: 15-min access token + 7-day HttpOnly refresh cookie. TenantQueryMiddleware resolves entity scope. 12 domain apps. drf-spectacular generates OpenAPI 3 schema.")
        ContainerQueue(broker, "Task Broker", "Redis 7 db1", "Celery message broker. Three named queues: default, integrations, reports.")
        Container(worker_d, "Default Worker", "Celery 4 concurrent", "Auth housekeeping, billing counter resets, inventory recomputation, milestone linking, notification pruning.")
        Container(worker_i, "Integrations Worker", "Celery 2 concurrent", "External API sync: Climatiq factors, Verra and Gold Standard registry serials, ECB/OER exchange rates.")
        Container(worker_r, "Reports Worker", "Celery 2 concurrent max-tasks-per-child=10", "PDF and CSV report rendering. Writes output to object storage. Purges expired report jobs.")
        Container(beat, "Task Scheduler", "Celery Beat DatabaseScheduler", "Dispatches 11 periodic tasks on schedule. beat_init validator confirms all schedule entries are registered before boot.")
        ContainerDb(pg, "Primary Database", "PostgreSQL 16 + PostGIS 3.4", "Single database with row-level multi-tenancy. ~70 tables across 12 apps. All querysets must filter by EntityId.")
        ContainerDb(redis_cache, "Cache & Result Store", "Redis 7 db0/db2/db3", "db0: API response cache. db2: Celery result backend. db3: Django cache framework.")
        ContainerDb(s3, "Object Storage", "Cloudflare R2 S3-compatible", "Report PDFs, CSV exports, file uploads. Path: node-id/entity-id/...")
    }

    System_Ext(ext, "External APIs", "Climatiq / Verra / Gold Standard / ECB / OER / GBIF / IUCN / Companies House / SMTP")

    Rel(user, nginx, "Accesses platform", "HTTPS 443")
    Rel(nginx, spa, "Serves Next.js pages and static assets", "HTTP")
    Rel(nginx, api, "Proxies /api/* requests", "HTTP Gunicorn")
    Rel(spa, nginx, "REST calls with JWT bearer + X-Entity-ID header", "HTTPS JSON")
    Rel(api, pg, "Reads and writes all tenant and platform data", "SQL Django ORM")
    Rel(api, redis_cache, "Response cache and Django cache", "Redis protocol")
    Rel(api, broker, "Enqueues background tasks", "Redis protocol")
    Rel(api, s3, "Stores file uploads, generates pre-signed download URLs", "S3 API")
    Rel(beat, broker, "Publishes 11 periodic tasks on schedule", "Redis protocol")
    Rel(broker, worker_d, "Dispatches default queue tasks")
    Rel(broker, worker_i, "Dispatches integrations queue tasks")
    Rel(broker, worker_r, "Dispatches reports queue tasks")
    Rel(worker_d, pg, "Reads and updates records", "SQL")
    Rel(worker_d, redis_cache, "Stores task results in db2", "Redis protocol")
    Rel(worker_i, pg, "Writes synced factor and registry data", "SQL")
    Rel(worker_i, ext, "Syncs emission factors, credit serials, FX rates", "HTTPS")
    Rel(worker_r, pg, "Reads all report data", "SQL")
    Rel(worker_r, s3, "Writes generated report files", "S3 API")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")`,
  },
  {
    id: "l3a",
    tab: "API Pipeline",
    level: "Level 3a",
    title: "API Request Pipeline",
    description:
      "Every authenticated request passes through this eight-stage pipeline in order. A failure at any stage returns an error immediately — the request never reaches the next stage.",
    chart: `C4Component
    title Component Diagram — Django API: Request Pipeline

    Container_Ext(spa, "Web Application", "Next.js 14", "Sends JWT bearer token and X-Entity-ID header on every request")
    ContainerDb_Ext(pg, "PostgreSQL", "PostgreSQL 16 + PostGIS", "RBAC tables, RevokedTokens, tenant data")

    Container_Boundary(api, "Django REST API") {
        Component(mw, "TenantQueryMiddleware", "Django Middleware", "Reads X-Entity-ID header. Validates that the requesting user is a member of that entity (or is SuperAdmin). Sets request.entity_id. Rejects mismatched entity access with 403.")
        Component(auth, "RevokedTokenJWTAuthentication", "DRF Authentication class", "Validates JWT signature and expiry. Queries RevokedTokens table by Jti UUID. Provides immediate server-side revocation independent of the 15-minute token lifetime.")
        Component(perm, "Permission Layer", "DRF Permissions", "IsSuperAdmin: checks Users.IsSuperAdmin flag only. HasModulePrivilege: resolves union across all active EntityUserRoles, RolePrivileges, Modules/Interfaces chain. UserPrivilegeOverrides applied last.")
        Component(gate, "FeatureGateMixin", "DRF ViewSet mixin", "Short-circuited when FEATURE_GATES_ENABLED=False (current default). When enabled: checks PlanFeatures table and returns HTTP 402 feature_gated if not entitled.")
        Component(mixin, "TenantViewSetMixin", "DRF ViewSet mixin", "Overrides get_queryset() to always append .filter(EntityId=request.entity_id, Status__lt=4). EntityId from request body is never trusted.")
        Component(views, "Domain ViewSets", "DRF ModelViewSet subclasses", "One ViewSet per domain model. EmissionsDataViewSet triggers server-side GHG calculation on every save. Verified inventories (VerificationStatus >= 3) reject PATCH/DELETE with HTTP 403.")
        Component(audit, "AuditLog", "Django Model + signals", "Records every create, update, and delete with actor UserId, EntityId, IP address, and before/after JSON snapshot. Three-tier retention enforced by daily purge task.")
        Component(spec, "OpenAPI Schema endpoint", "drf-spectacular", "Generates OpenAPI 3 spec at /api/schema/. Frontend build runs orval against this spec to emit typed TypeScript client and TanStack Query hooks.")
    }

    Rel(spa, mw, "Authenticated REST request", "JWT bearer + X-Entity-ID header")
    Rel(mw, pg, "Validates entity membership for non-superadmin users", "SQL")
    Rel(mw, auth, "Passes request with entity_id resolved")
    Rel(auth, pg, "Checks RevokedTokens by Jti UUID", "SQL")
    Rel(auth, perm, "Passes authenticated user and token")
    Rel(perm, pg, "Reads Modules, Interfaces, RolePrivileges, EntityUserRoles", "SQL")
    Rel(perm, gate, "Passes privileged request")
    Rel(gate, mixin, "Passes or returns HTTP 402")
    Rel(mixin, views, "Delivers entity-scoped queryset")
    Rel(views, pg, "Tenant-scoped reads and writes via Django ORM", "SQL")
    Rel(views, audit, "Logs every mutation")
    Rel(spec, spa, "OpenAPI 3 spec consumed by orval at build time", "HTTPS JSON")`,
  },
  {
    id: "l3b",
    tab: "Domain Apps",
    level: "Level 3b",
    title: "Django Domain Apps",
    description:
      "The twelve Django apps in INSTALLED_APPS load order. Apps earlier in the list are depended on by apps later — no reverse imports.",
    chart: `C4Component
    title Component Diagram — Django API: Domain Apps

    Container_Boundary(api, "Django REST API — 12 Domain Apps") {
        Component(shared, "shared", "Django App 1st", "GWPDatasets, Units, EmissionFactorLibrary, Modules, Interfaces, Currencies, SharedDocuments, Tags. Platform-wide reference data with no tenant ownership.")
        Component(entities, "entities", "Django App 2nd", "Entities (self-referential hierarchy, types 1-8), RelatedEntities peer graph, EntityMembers (multi-entity user access), EntityLocations, EntityContacts, EntityDocuments. Multi-tenancy root.")
        Component(users, "users", "Django App 3rd", "Users, Roles, RolePrivileges, EntityUserRoles, UserPrivilegeOverrides. JWT issuance and revocation. RBAC privilege resolution via HasModulePrivilege.")
        Component(projects, "projects", "Django App 4th", "DevelopmentProjects, ProjectPhases, DevelopmentProjectPartners. Links EmissionsData and LandParcels to a project context. Supports partner share and double-counting flags.")
        Component(land, "land", "Django App 5th", "LandParcels, LandParcelActivities, LandCoverTypes. Geospatial polygon storage via PostGIS. Parcel activity timeline for LULUCF accounting.")
        Component(ecosystem, "ecosystem", "Django App 6th", "Ecosystems, EcosystemTrees (removals and planting records), SpeciesObservations, GBIF sync state. TNFD-aligned biodiversity tracking.")
        Component(emissions, "emissions", "Django App 7th", "EmissionsData (Scope 1/2/3), GHGInventories (formal reporting periods), Scope3CategoryRelevance, TargetMilestones. Server-side GHG calculation engine. Biogenic CO2 tracked separately.")
        Component(restorations, "restorations", "Django App 8th", "RestorationProjects, RestorationPlantings, BiomassCarbon. IPCC LULUCF biomass carbon sequestration calculations for restoration activities.")
        Component(notifications, "notifications", "Django App 9th", "Notifications, NotificationTemplates. In-app alerts triggered by verification events, report completion, system events, and billing threshold crossings.")
        Component(blog, "blog", "Django App 10th", "BlogPosts, BlogCategories. Draft/pending/published state machine. Rich-text content management for the marketing site.")
        Component(reports, "reports", "Django App 11th", "ReportJobs, ReportTemplates. Async PDF and CSV generation queued via Celery reports queue. Pre-signed S3 download URLs with configurable expiry.")
        Component(billing, "billing", "Django App 12th", "Plans, PlanFeatures, Subscriptions, UsageTracking. Plan limit resolution: MaxEntities, MaxUsersPerEntity, MaxReportingYears, MaxApiCallsPerDay. Limit enforcement callers present but not yet wired.")
    }`,
  },
  {
    id: "l3c",
    tab: "Workers",
    level: "Level 3c",
    title: "Celery Async Worker Layer",
    description:
      "How background tasks are structured, scheduled, and routed across three worker pools. The beat_init validator ensures all schedule entries are registered before the scheduler starts.",
    chart: `C4Component
    title Component Diagram — Celery Async Worker Layer

    ContainerDb_Ext(pg, "PostgreSQL", "PostgreSQL 16", "Source for all sync, calculation, and report data")
    ContainerDb_Ext(broker, "Redis db1", "Celery broker", "Inbound task queues: default, integrations, reports")
    ContainerDb_Ext(results, "Redis db2", "Celery result backend", "Task result storage")
    ContainerDb_Ext(s3, "Object Storage", "Cloudflare R2", "Report PDF and CSV output")
    System_Ext(ext, "External APIs", "Climatiq / Verra / Gold Standard / ECB / OER")

    Container_Boundary(workers, "Celery Worker Layer") {
        Component(beat, "celery beat", "Celery Beat DatabaseScheduler", "Dispatches 11 scheduled tasks. beat_init validator ensures every beat_schedule entry is registered before the scheduler starts.")
        Component(w_auth, "tasks.auth", "Default queue", "purge_expired_revoked_tokens 05:00 daily. purge_expired_audit_logs 05:30 daily (enforces three-tier retention). prune_old_notifications 05:45 daily.")
        Component(w_billing, "tasks.billing", "Default queue", "reset_daily_api_counters 00:00 daily. Resets UsageTracking per-tenant day counters.")
        Component(w_emissions, "tasks.emissions", "Default queue", "recompute_stale_inventory_totals 01:00 daily: re-aggregates scope totals into GHGInventories. link_milestone_actuals 01:30 daily: fills TargetMilestones.ActualEmissionsTonnes.")
        Component(w_climatiq, "tasks.integrations.climatiq", "Integrations queue", "sync_climatiq_emission_factors 02:00 UTC every Sunday. Refreshes EmissionFactorLibrary from the Climatiq API.")
        Component(w_registry, "tasks.integrations.verra_gs", "Integrations queue", "sync_verra_registry 03:00 daily. sync_gold_standard_registry 03:30 daily. Validates active credit serials against registry APIs.")
        Component(w_fx, "tasks.integrations.fx", "Integrations queue", "sync_ecb_fx_rates 17:00 daily. sync_oer_fx_rates on demand. Writes daily exchange rates to Currencies rows.")
        Component(w_reports, "tasks.reports", "Reports queue max-tasks-per-child=10", "generate_report on demand: renders PDF/CSV, uploads to S3, updates job status. purge_expired_reports 04:00 daily.")
    }

    Rel(beat, broker, "Publishes scheduled tasks to named queues", "Redis protocol")
    Rel(broker, w_auth, "default queue")
    Rel(broker, w_billing, "default queue")
    Rel(broker, w_emissions, "default queue")
    Rel(broker, w_climatiq, "integrations queue")
    Rel(broker, w_registry, "integrations queue")
    Rel(broker, w_fx, "integrations queue")
    Rel(broker, w_reports, "reports queue")
    Rel(w_auth, pg, "Sweeps expired token and audit records", "SQL")
    Rel(w_billing, pg, "Resets UsageTracking counters", "SQL")
    Rel(w_emissions, pg, "Reads EmissionsData, writes GHGInventories totals", "SQL")
    Rel(w_climatiq, ext, "Fetches updated emission factors from Climatiq", "HTTPS REST")
    Rel(w_climatiq, pg, "Writes EmissionFactorLibrary rows", "SQL")
    Rel(w_registry, ext, "Validates credit serial numbers against registry APIs", "HTTPS REST")
    Rel(w_registry, pg, "Updates credit validation status", "SQL")
    Rel(w_fx, ext, "Fetches daily FX rates", "HTTPS REST")
    Rel(w_fx, pg, "Writes Currencies exchange rate rows", "SQL")
    Rel(w_reports, pg, "Reads all data required to render the report", "SQL")
    Rel(w_reports, s3, "Uploads rendered report file", "S3 API")
    Rel(w_reports, results, "Stores task result and final job status", "Redis protocol")`,
  },
  {
    id: "l4",
    tab: "GHG Calculation",
    level: "Level 4",
    title: "GHG Calculation Pipeline",
    description:
      "The most security-critical code path: the client never computes or submits EmissionsAmount. It submits raw activity data and receives back a fully calculated, server-authoritative record.",
    chart: `flowchart TD
    subgraph L1["Browser — data contributor"]
        UI["POST /api/emissions/ or PATCH /api/emissions/id/\nScope, activity quantity, unit, emission factor reference,\nsupplier, period, project, phase, inventory assignment"]
    end

    subgraph L2["Serializer — boundary validation"]
        S1["Reject unknown request fields (400)"]
        S2["Overwrite EntityId with request.entity_id\nbody EntityId never trusted"]
        S3["Cross-reference check\nProject, phase, and inventory must all\nbelong to the same entity"]
        S4["GWP dataset resolution\nAdopt inventory GWP dataset if assigned,\nelse active system default from GWPDatasets"]
        S1 --> S2 --> S3 --> S4
    end

    subgraph L3["EmissionsData.save() override"]
        CALC["compute_emissions() called on every save\nAll result columns are overwritten"]
        UNIT["Unit conversion\nInputUnitId to QuantityCanonical\ncanonical SI unit per activity type"]
        GWP["GWP factor lookup\nGWPDatasets x GasType x Subtype\nglobal warming potential"]
        CORE["Core formula\nkg CO2e = QuantityCanonical\n          x EmissionFactor\n          x GWP"]
        BIO{"Biogenic\nfactor?"}
        BIO_CALC["BiogenicCO2AmountTonnes\nComputed separately\nNOT added to the CO2e total"]
        S2_CHECK{"Scope 2?"}
        S2_BOTH["Compute both result columns\nEmissionsAmountLocationBased\nEmissionsAmountMarketBased\nFallback documented where one\nmethod factor is absent"]
        CALC --> UNIT --> GWP --> CORE
        CORE --> BIO
        BIO -->|Yes| BIO_CALC --> S2_CHECK
        BIO -->|No| S2_CHECK
        S2_CHECK -->|Yes| S2_BOTH
        S2_CHECK -->|No| PERSIST
        S2_BOTH --> PERSIST
    end

    subgraph L4["Persistence"]
        PERSIST[("INSERT / UPDATE emissions_data\nSource inputs round-trip unchanged\nResult columns overwritten by server")]
        AUDIT[("AuditLog CREATE event\nActorId, EntityId, IP, before/after JSON")]
        LOCK["Immutability guard\nIf GHGInventories.VerificationStatus >= 3\nPATCH/DELETE return HTTP 403"]
    end

    UI --> S1
    S4 -->|Validated payload| CALC
    PERSIST --> AUDIT
    AUDIT --> LOCK

    style BIO_CALC fill:#e8f5e9,stroke:#1b5e20,color:#000
    style S2_BOTH fill:#e3f2fd,stroke:#0d47a1,color:#000
    style PERSIST fill:#f3e5f5,stroke:#4a148c,color:#000
    style AUDIT fill:#fff3e0,stroke:#e65100,color:#000
    style LOCK fill:#ffebee,stroke:#b71c1c,color:#000`,
  },
];

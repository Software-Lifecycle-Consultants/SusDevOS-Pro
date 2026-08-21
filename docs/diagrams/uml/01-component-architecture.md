# 01 — Component & Deployment Architecture

How the running system is composed. Everything inside **SusDevOS Platform** is code in this
repo; everything in **External Services** is a third party reached over HTTPS.


**Related user stories** — [Billing & platform — SDO-BIL-12, 13](../../stories/06-billing-platform.md)

```mermaid
flowchart TB
    subgraph Client["Client tier"]
        BROWSER["Browser<br/>Next.js 14 App Router"]
    end

    subgraph Frontend["Frontend — frontend/ (Node 20)"]
        PAGES["App Router pages<br/>(app) · (marketing) · (public)"]
        QUERY["TanStack Query hooks<br/>src/hooks/"]
        ORVAL["Generated API client<br/>src/lib/api (orval)"]
        ZUSTAND["Auth store<br/>src/store/auth.ts"]
        PAGES --> QUERY --> ORVAL
        PAGES --> ZUSTAND
    end

    subgraph Backend["Backend — backend/ (Django 5.1 + DRF)"]
        MW["TenantQueryMiddleware<br/>sets request.entity_id"]
        AUTH["RevokedTokenJWTAuthentication<br/>checks RevokedTokens by Jti"]
        PERM["Permission layer<br/>HasModulePrivilege · IsSuperAdmin"]
        GATE["FeatureGateMixin<br/>402 feature_gated"]
        VIEWS["ViewSets<br/>TenantViewSetMixin"]
        SVC["Service layer<br/>apps/*/services.py"]
        MODELS["Models<br/>~70 tables"]
        SPEC["drf-spectacular<br/>/api/schema/"]

        MW --> AUTH --> PERM --> GATE --> VIEWS --> SVC --> MODELS
        VIEWS -.-> SPEC
    end

    subgraph Workers["Celery workers"]
        WDEF["default queue<br/>-c 4"]
        WINT["integrations queue<br/>-c 2"]
        WREP["reports queue<br/>-c 2, max-tasks-per-child=10"]
        BEAT["celery beat<br/>DatabaseScheduler"]
    end

    subgraph Data["Data tier"]
        PG[("PostgreSQL 16<br/>+ PostGIS 3.4")]
        REDIS[("Redis 7<br/>db0 cache · db1 broker<br/>db2 results · db3 django-cache")]
        S3[("S3 / MinIO<br/>node-id/entity-id/...")]
    end

    subgraph External["External services"]
        CLIMATIQ["Climatiq<br/>emission factors"]
        VERRA["Verra VCS registry"]
        GS["Gold Standard registry"]
        ECB["ECB / OER<br/>FX rates"]
        GBIF["GBIF + IUCN<br/>species data"]
        CH["Companies House"]
        SMTP["SMTP / SES"]
    end

    BROWSER --> PAGES
    ORVAL -->|"JWT bearer<br/>+ X-Entity-ID"| MW
    ORVAL -->|"refresh_token cookie<br/>HttpOnly, /api/auth/refresh"| AUTH

    MODELS --> PG
    VIEWS --> REDIS
    VIEWS -->|"enqueue"| REDIS
    REDIS --> WDEF & WINT & WREP
    BEAT -->|"schedules"| REDIS

    WREP --> S3
    WREP --> PG
    WDEF --> PG
    WINT --> PG

    WINT --> CLIMATIQ & VERRA & GS & ECB
    VIEWS --> GBIF & CH
    WDEF --> SMTP

    classDef ext fill:#fff3e0,stroke:#e65100,color:#000
    classDef data fill:#e8f5e9,stroke:#1b5e20,color:#000
    class CLIMATIQ,VERRA,GS,ECB,GBIF,CH,SMTP ext
    class PG,REDIS,S3 data
```

## Request pipeline order — and why it matters

`TenantQueryMiddleware` is **Django** middleware, so it runs *before* DRF authenticates the
request. On a JWT request `request.user` is still anonymous at middleware time, so the
middleware cannot resolve the entity. Every tenant-scoped view therefore re-resolves it:

```mermaid
flowchart LR
    A["Django middleware<br/>TenantQueryMiddleware"] -->|"user still<br/>AnonymousUser"| B["entity_id = None"]
    B --> C["DRF dispatch"]
    C --> D["initial()<br/>auth + permissions run"]
    D --> E["EntityScopeInitialMixin<br/>resolve_request_entity_id()"]
    E --> F["entity_id now correct"]
    F --> G["get_queryset()<br/>.filter(EntityId=entity_id)"]

    style E fill:#fff3e0,stroke:#e65100,color:#000
```

Omitting `EntityScopeInitialMixin` on a tenant-scoped view does not raise — it silently
yields `entity_id is None`, which produces empty reads and NOT-NULL violations on create.

## Deployment topology (local)

| Service | Image / runtime | Host port | Notes |
|---------|-----------------|-----------|-------|
| `db` | `postgis/postgis:16-3.4` | *none* | Internal only — reachable as `db:5432` |
| `redis` | `redis:7-alpine` | 6379 | 4 logical DBs |
| `minio` | `minio/minio:latest` | 9000 / 9001 | S3 API / console |
| `api` | `backend/Dockerfile` | 8000 | `runserver`, `config.settings.local` |
| `celery_worker` | `backend/Dockerfile` | — | `default` queue |
| `celery_integrations` | `backend/Dockerfile` | — | `integrations` queue |
| `celery_reports` | `backend/Dockerfile` | — | `reports` queue |
| `celery_beat` | `backend/Dockerfile` | — | `django_celery_beat` DatabaseScheduler |
| frontend | Node 20 on host | 3000 | Not containerised for dev |

`db` deliberately publishes no host port — 5432/5433 are occupied by other local databases.
Backend processes must run inside the compose network to reach it.

---
*Source: `docker-compose.yml`, `backend/config/settings/`, `backend/config/celery.py`,
`backend/apps/entities/middleware.py`, `backend/apps/shared/views.py`,
`backend/apps/users/authentication.py`, `frontend/src/`*

# 06 · Billing & Platform

Plans, entitlement, feature gates, usage limits, the public CMS, and the API contract.

Conventions, statuses and the story template are defined in [README.md](README.md).

---

## Plans & entitlement

<a id="sdo-bil-01"></a>

### SDO-BIL-01 · Anyone can see what the plans cost

**As a** prospect
**I want** to read the pricing without an account
**so that** I can decide whether to sign up.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Public — `AllowAny` |
| **Diagram** | [UML 05 — billing](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/billing/views.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** an unauthenticated request to `/api/billing/plans/`, **when** it is made,
   **then** it returns 200 with the plans marked `IsPublic`.
2. **Given** a non-public plan, **when** the list is fetched anonymously, **then** it is absent.

<a id="sdo-bil-02"></a>

### SDO-BIL-02 · A new entity starts on the free plan

**As a** new customer
**I want** a working account immediately after signing up
**so that** I can evaluate the product before paying.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [BPMN 01 — onboarding](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/users/services.py` · `register_new_entity()` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a new entity, **when** it is created, **then** an `EntitySubscriptions` row is
   attached with `Status = "active"`.
2. **Given** the free plan has not been seeded, **when** entity creation is attempted,
   **then** it fails — `seed_plans` is a hard prerequisite, which is why the seed order is
   `seed_superadmins → seed_modules → seed_gwp → seed_plans`.
3. **Given** the OneToOne on `EntityId`, **when** a second subscription is attempted for the
   same entity, **then** it is rejected.

<a id="sdo-bil-03"></a>

### SDO-BIL-03 · A gated feature returns a structured upgrade prompt

**As a** user on a plan without a feature
**I want** a clear upgrade path rather than a generic error
**so that** I know what to do next.

| | |
|---|---|
| **Status** | ✅ Built — status code documented by [F5](../diagrams/FINDINGS.md#f5) |
| **Diagram** | [UML 05 — gate enforcement path](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/billing/mixins.py` · `backend/apps/shared/exceptions.py` |
| **Tests** | `backend/apps/emissions/tests/test_ghg_inventory.py` · `backend/apps/reports/tests/test_feature_gate.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a gated view and an entity lacking the feature, **when** it is called,
   **then** the response is **402 Payment Required**.
2. **Given** that response, **when** it is parsed, **then** it carries `code`
   (`"feature_gated"`), `feature`, `detail` and `upgrade_url`.
3. **Given** the frontend receives it, **when** rendering, **then** it shows the upgrade modal
   rather than a generic failure.

<a id="sdo-bil-04"></a>

### SDO-BIL-04 · Gates are enforced by the server, never the client

**As a** platform owner
**I want** entitlement checked server-side
**so that** a modified client cannot unlock paid features.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 05](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/billing/mixins.py` · `FeatureGateMixin.initial()` |
| **Linear** | `area:bil` · `type:spec` · `risk:billing` |

**Acceptance criteria**

1. **Given** a gated endpoint, **when** called directly with a valid token by an entity lacking
   the feature, **then** it is refused regardless of what the client UI allows.
2. **Given** the mixin, **when** `initial()` runs, **then** authentication and permissions are
   evaluated **before** the gate, so an anonymous caller gets 401 rather than 402.

> This principle is currently applied to *feature gates* but not to *role privileges* — see
> [SDO-GAP-01](07-backlog-gaps.md#sdo-gap-01), where the same reasoning has not been extended.

<a id="sdo-bil-05"></a>

### SDO-BIL-05 · SuperAdmin bypasses every gate

**As a** support engineer
**I want** to reproduce a customer's problem without changing their plan
**so that** I can diagnose without side effects.

| | |
|---|---|
| **Status** | ✅ Built |
| **Code** | `backend/apps/billing/mixins.py` — the `SUPERADMIN_BYPASS` branch |
| **Tests** | `backend/apps/emissions/tests/test_ghg_inventory.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a SuperAdmin, **when** they call any gated endpoint, **then** the gate does not
   apply, whatever the target entity's plan.

<a id="sdo-bil-06"></a>

### SDO-BIL-06 · A past-due account keeps access until the period it paid for ends

**As a** customer whose card has just failed
**I want** to keep working until the period I paid for runs out
**so that** a billing hiccup does not halt my reporting mid-cycle.

| | |
|---|---|
| **Status** | ✅ Built — introduced by [F8](../diagrams/FINDINGS.md#f8) |
| **Diagram** | [UML 07 §7.7 — subscription states](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/billing/services.py` · `get_entitled_subscription()` |
| **Tests** | `backend/apps/billing/tests/test_entitlement.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** `Status = "past_due"` and `CurrentPeriodEnd` in the future, **when** entitlement is
   resolved, **then** the subscription still confers its plan's features.
2. **Given** `Status = "past_due"` and `CurrentPeriodEnd` in the past, **when** resolved,
   **then** features are denied.
3. **Given** `Status = "past_due"` and `CurrentPeriodEnd` is `NULL`, **when** resolved,
   **then** features are denied — no open-ended grace.

> Nothing in the platform currently *sets* `past_due`; see
> [SDO-GAP-05](07-backlog-gaps.md#sdo-gap-05). This behaviour is correct and tested but
> unreachable until a payment provider is wired in.

<a id="sdo-bil-07"></a>

### SDO-BIL-07 · Subscription status determines entitlement

**As a** platform owner
**I want** one place that decides whether an account is entitled
**so that** the rule cannot drift between callers.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 07 §7.7](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/billing/services.py` · `ENTITLED_STATUSES`, `get_entitled_subscription()` |
| **Tests** | `backend/apps/billing/tests/test_entitlement.py` |
| **Linear** | `area:bil` · `type:spec` |

Vocabulary: `active`, `trialing`, `past_due`, `canceled`, `incomplete` — note the single-L
spelling of `canceled`.

**Acceptance criteria**

1. **Given** `active` or `trialing`, **when** resolved, **then** entitled.
2. **Given** `canceled` or `incomplete`, **when** resolved, **then** not entitled, regardless of
   `CurrentPeriodEnd`.
3. **Given** no subscription row at all, **when** resolved, **then** not entitled.
4. **Given** any caller needing entitlement, **when** it checks, **then** it goes through
   `get_entitled_subscription()` rather than repeating the status filter.

<a id="sdo-bil-08"></a>

### SDO-BIL-08 · API usage is counted against the plan's daily limit

**As a** platform owner
**I want** API consumption metered per entity
**so that** a single tenant cannot exhaust shared capacity.

| | |
|---|---|
| **Status** | 🟡 Partial — implemented; no test covers the limit being reached |
| **Diagram** | [UML 05 — billing](../diagrams/uml/05-domain-platform.md) · [UML 08](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/apps/billing/services.py` · `record_api_call()` · `tasks.billing.reset_daily_api_counters` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a metered call, **when** it is recorded, **then** `UsageTracking.ApiCallsToday`
   increments for that entity.
2. **Given** `Plans.MaxApiCallsPerDay` is reached, **when** another call is made, **then** it is
   refused.
3. **Given** midnight UTC, **when** `reset_daily_api_counters` runs, **then** `ApiCallsToday`
   resets while `ApiCallsMonth` is preserved.
4. **Given** no entitled subscription resolves, **when** usage is checked, **then** the limit is
   `0` and calls are refused — this fails **closed**, unlike `can_add_entity()`.

<a id="sdo-bil-09"></a>

### SDO-BIL-09 · Entity-count limits apply when adding entities

**As a** platform owner
**I want** the number of entities to respect the plan
**so that** a group structure cannot be built on a single-entity plan.

| | |
|---|---|
| **Status** | 🟡 Partial — enforced when a plan resolves; **fails open** when none does |
| **Diagram** | [UML 05](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/billing/services.py` · `can_add_entity()` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a plan with `MaxEntities`, **when** the count is below it, **then** adding is
   allowed.
2. **Given** the count is at the limit, **when** adding is attempted, **then** it is refused.
3. **Given** no entitled subscription resolves, **when** adding is attempted, **then** it is
   currently **allowed** — a deliberate asymmetry against `SDO-BIL-08`, tracked as
   [SDO-GAP-04](07-backlog-gaps.md#sdo-gap-04).

---

## Content & contract

<a id="sdo-bil-10"></a>

### SDO-BIL-10 · Author, publish and archive a blog post

**As a** marketing author
**I want** to manage posts in the product
**so that** the public site has content without a separate CMS.

| | |
|---|---|
| **Status** | 🟡 Partial — implemented; `backend/apps/blog/` has no test package |
| **Diagram** | [UML 07 §7.5 — blog states](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/blog/views.py` |
| **Linear** | `area:bil` · `type:spec` |

`BlogStatus`: 1 Draft · 2 Published · 3 Archived.

**Acceptance criteria**

1. **Given** a draft, **when** it is published, **then** `BlogStatus = 2` and `PublishedAt` is
   set.
2. **Given** a published post, **when** archived, **then** `BlogStatus = 3`.
3. **Given** a post, **when** created, **then** `AuthorId` and `EntityId` come from the request
   context, not the body.

<a id="sdo-bil-11"></a>

### SDO-BIL-11 · Only published posts are served publicly

**As a** site visitor
**I want** to read published articles without an account
**so that** the marketing site works for anonymous readers.

| | |
|---|---|
| **Status** | 🟡 Partial — implemented; untested |
| **Diagram** | [UML 05 — blog/CMS](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/blog/urls_public.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a published post, **when** requested anonymously at
   `/api/public/blog/{slug}/`, **then** it returns 200.
2. **Given** a draft or archived post, **when** requested at the same path, **then** it is not
   found — draft content must never leak through the public router.

<a id="sdo-bil-12"></a>

### SDO-BIL-12 · Local development publishes the schema used for client generation

**As a** frontend developer
**I want** a typed client generated from the live API
**so that** the contract cannot drift silently.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 01 — component architecture](../diagrams/uml/01-component-architecture.md) |
| **Code** | drf-spectacular · `frontend/orval.config.ts` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** a local `DEBUG=True` API, **when** `/api/schema/` is fetched, **then** it returns a
   valid OpenAPI 3 document; Swagger UI and ReDoc render locally.
2. **Given** production Django/Nginx, **when** the schema, Swagger, or ReDoc path is fetched,
   **then** it returns `404` because customer/developer API access is deferred.
3. **Given** the local schema, **when** `npm run generate` is run, **then** the TypeScript client and
   TanStack Query hooks in `frontend/src/lib/api/` are regenerated.

<a id="sdo-bil-13"></a>

### SDO-BIL-13 · Housekeeping runs nightly without operator action

**As an** operator
**I want** retention and cleanup to run on a schedule
**so that** compliance obligations are met without manual work.

| | |
|---|---|
| **Status** | ✅ Built — schedule completed by [F7](../diagrams/FINDINGS.md#f7) |
| **Diagram** | [UML 08 — beat schedule](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/config/celery.py` · `backend/tasks/auth.py` |
| **Tests** | `backend/tasks/tests/test_beat_schedule.py` |
| **Linear** | `area:bil` · `type:spec` |

**Acceptance criteria**

1. **Given** the audit log, **when** `purge_expired_audit_logs` runs at 05:30, **then** rows are
   removed per their `RetentionTier` — 30 days, 1 year, or 7 years.
2. **Given** revoked tokens whose underlying JWT has expired, **when** the 05:00 task runs,
   **then** they are swept.
3. **Given** read notifications past their window, **when** `prune_old_notifications` runs at
   05:45, **then** they are trimmed.
4. **Given** the schedule, **when** beat starts, **then** every task it names is registered —
   enforced at `beat_init` and asserted in CI.

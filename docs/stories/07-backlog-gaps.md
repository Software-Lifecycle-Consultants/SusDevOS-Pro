# 07 · Backlog & Gaps

Known gaps, undecided policy, and drift risks. Everything here is **not built** or **not
decided** — the ✅ Built behaviour lives in epics 01–06.

Each item is written as a story so it can move straight into Linear. Items are ordered by
severity within each section, not by ID.

> These come from three places: deriving the [diagram set](../diagrams/README.md) from source,
> fixing the ten findings in [FINDINGS.md](../diagrams/FINDINGS.md), and writing epics 01–06.
> Nothing here is speculative — each names the code that does or does not exist.

---

## Security & correctness

<a id="sdo-gap-01"></a>

### SDO-GAP-01 · The RBAC privilege system is not enforced at any endpoint

**As a** platform owner
**I want** the privilege model that the product is sold on to actually gate the API
**so that** a user cannot perform an action their role forbids by calling the endpoint directly.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Severity** | High — the seeded privilege model is currently decorative |
| **Diagram** | [UML 02 — privilege resolution](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/shared/permissions.py` · `HasModulePrivilege` |
| **Linear** | [SUS-5](https://linear.app/susdevos/issue/SUS-5) · `area:ten` · `type:bug` · `risk:security` |

The database seeds **13 modules, 50 interfaces and 56 role-privilege rows**, and
`_resolve_privilege()` implements the full override-then-role resolution algorithm. But
`HasModulePrivilege` — the only class that consults it — **appears nowhere except its own
docstring examples**. Across the app views, 27 viewsets declare bare
`permission_classes = [IsAuthenticated]`.

What the privilege system actually drives today is `build_privilege_map()`, which feeds
`GET /auth/me` and populates the frontend Zustand store. That is **frontend-only gating** —
the exact thing `CLAUDE.md` forbids for feature gates ("Feature gates are server-enforced.
Never rely on frontend-only gating"). The same reasoning applies here, but the rule was never
extended to privileges.

Coarse role checks (`IsEntityAdmin`, `IsManagerOrAbove`, `IsSuperAdmin`) *are* enforced, but
only in three files: `users/views.py`, `entities/views.py`, `emissions/views.py`. Everywhere
else, any authenticated member of a tenant can call any endpoint for that tenant.

**Acceptance criteria**

1. **Given** a Staff user whose role has no `create_` privilege for a module,
   **when** they POST to that module's endpoint,
   **then** the response is 403 — not 201.
2. **Given** the interface catalogue,
   **when** the enforcement work is complete,
   **then** every non-public viewset declares an explicit privilege requirement, and a test
   asserts no viewset falls back to bare `IsAuthenticated` unintentionally.
3. **Given** a user whose frontend privilege map hides an action,
   **when** they call the endpoint directly with a valid token,
   **then** the server refuses independently of the map.

**Notes.** This is the largest piece of work in the backlog and should be sequenced
deliberately — retrofitting 27 viewsets risks breaking working flows. Consider an
allow-list-per-viewset migration with the map-vs-enforcement mismatch logged before it is
enforced, so the gap can be measured before it is closed.

<a id="sdo-gap-02"></a>

### SDO-GAP-02 · Orphaned ecosystem/species rows will block the F1 migration

**As a** deployer
**I want** to know before deploying whether any `ecosystem` or `species` row points at a
missing entity
**so that** the new foreign-key constraint does not fail mid-migration in production.

| | |
|---|---|
| **Status** | ⬜ Gap — pre-deployment task |
| **Severity** | High — blocks a deploy, but only once |
| **Diagram** | [UML 04](../diagrams/uml/04-domain-nature-mrv.md) · [F1](../diagrams/FINDINGS.md#f1) |
| **Code** | `backend/apps/ecosystem/migrations/0004_*.py` |
| **Linear** | [SUS-6](https://linear.app/susdevos/issue/SUS-6) · `area:nat` · `type:task` · `risk:schema` |

`EntityId` on both models became a real `ForeignKey`. The migration adds the constraint to an
existing column, so any pre-existing row referencing a deleted entity will abort it. The local
database has zero rows in both tables, so this cannot surface in development.

**Acceptance criteria**

1. **Given** the production database,
   **when** the orphan check runs before migrating,
   **then** it reports the count of `ecosystem` and `species` rows whose `EntityId` has no
   matching `entities` row.
2. **Given** any orphans exist,
   **when** they are remediated,
   **then** `migrate` applies `ecosystem/0004` without error.

<a id="sdo-gap-03"></a>

### SDO-GAP-03 · A manager can verify their own emissions record

**As an** assurance provider
**I want** verification to be performed by someone other than the record's author
**so that** the verification signature carries independent weight.

| | |
|---|---|
| **Status** | ❓ Undecided — product decision |
| **Diagram** | [BPMN 02](../diagrams/bpmn/02-emissions-lifecycle.md) · [F10](../diagrams/FINDINGS.md#f10) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet.get_permissions` |
| **Linear** | [SUS-14](https://linear.app/susdevos/issue/SUS-14) · `area:inv` · `type:decision` |

Verification is now restricted to Manager and above (F10), which closed the worst of the gap —
Staff can no longer sign off their own work. But a Manager who records a figure can still
verify it.

The trade-off is real: in a small team one person legitimately does both, and blocking it
would stop them dead. Segregation of duties is a policy question, not a defect.

**Acceptance criteria** *(only if the decision is to enforce it)*

1. **Given** a record whose `CreatedBy` is the requesting user,
   **when** they POST to `/verify/`,
   **then** the response is 403 with a distinct code such as `self_verification_denied`.
2. **Given** an entity with only one Manager,
   **when** that policy would deadlock them,
   **then** a documented escalation exists — SuperAdmin verification, or a per-entity opt-out.

<a id="sdo-gap-04"></a>

### SDO-GAP-04 · No plan limit is enforced anywhere

**As a** platform owner
**I want** the limits I sell to actually bind
**so that** a tier means something operationally, not just on the pricing page.

| | |
|---|---|
| **Status** | ⬜ Gap — nothing enforces plan limits |
| **Diagram** | [UML 05 — gate enforcement](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/billing/services.py` · `can_add_entity()` · `record_api_call()` |
| **Linear** | [SUS-15](https://linear.app/susdevos/issue/SUS-15) · `area:bil` · `type:decision` · `risk:billing` |

Originally filed as an *asymmetry*: `is_feature_enabled()` and `record_api_call()` fail
closed when no entitled subscription resolves, while `can_add_entity()` fails open.

Re-checked when per-capability gating was switched off, and the finding is larger than the
asymmetry. **`can_add_entity()` and `record_api_call()` have no callers anywhere in the
codebase**, and `MaxUsersPerEntity` / `MaxReportingYears` are stored, seeded and serialized
but never compared against anything. `record_api_call()` was wired to the API-key path,
which went away when customer API access was disabled. So today:

| Limit | Enforced? |
|---|---|
| `MaxEntities` | No — `can_add_entity()` is never called |
| `MaxApiCallsPerDay` | No — `record_api_call()` is never called, and there is no customer API |
| `MaxUsersPerEntity` | No — never compared |
| `MaxReportingYears` | No — never compared |

This matters more now, not less: with capability gating off, these quantitative limits are
the *only* thing a service/hosting tier could be built on. The fail-open/fail-closed
question is downstream of first giving the helpers a caller.

The grace-period policy they resolve through (`get_entitled_subscription()`, FIX F8) is
tested and correct — see `backend/apps/billing/tests/test_entitlement.py` — so the
behaviour is pinned and ready for whenever the limits are wired in.

**Acceptance criteria**

1. **Given** an entity with no entitled subscription,
   **when** it attempts to add another entity,
   **then** the behaviour matches the documented decision — and a test pins it either way.

---

## Billing

<a id="sdo-gap-05"></a>

### SDO-GAP-05 · No payment provider ever sets a subscription status

**As a** finance owner
**I want** subscription status to reflect what actually happened to the payment
**so that** entitlement follows billing reality instead of being set by hand.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Severity** | High — the entire billing state machine is currently inert |
| **Diagram** | [UML 07 — subscription states](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/billing/models.py` · `EntitySubscriptions.Status` |
| **Linear** | [SUS-7](https://linear.app/susdevos/issue/SUS-7) · `area:bil` · `type:feature` |

`EntitySubscriptions` carries `StripeCustomerId`, `StripeSubscriptionId` and
`StripeLatestInvoiceId`, and the status vocabulary includes `past_due`, `canceled` and
`incomplete`. But there is **no Stripe SDK usage, no webhook receiver, and no dunning logic
anywhere in the repo** — nothing ever transitions a subscription out of `active`.

This makes the F8 grace-period fix forward-looking: correct, tested, and currently unreachable.

**Acceptance criteria**

1. **Given** a Stripe `invoice.payment_failed` webhook,
   **when** it is received and verified,
   **then** the matching subscription moves to `past_due` and `CurrentPeriodEnd` is recorded.
2. **Given** a `customer.subscription.deleted` webhook,
   **when** received,
   **then** the subscription moves to `canceled` and entitlements stop.
3. **Given** any webhook,
   **when** its signature does not verify,
   **then** it is rejected without mutating state.

<a id="sdo-gap-06"></a>

### SDO-GAP-06 · A past-due customer gets no warning before access stops

**As a** customer whose card has failed
**I want** to be told before my features stop working
**so that** the first sign is not an upgrade modal mid-task.

| | |
|---|---|
| **Status** | ⬜ Gap — depends on [SDO-GAP-05](#sdo-gap-05) |
| **Diagram** | [UML 07](../diagrams/uml/07-state-machines.md) · [F8](../diagrams/FINDINGS.md#f8) |
| **Linear** | [SUS-13](https://linear.app/susdevos/issue/SUS-13) · `area:bil` · `type:feature` |

F8 gives `past_due` entitlements until `CurrentPeriodEnd`. Nothing tells the user that window
exists or when it closes. The notification vocabulary has no billing type.

**Acceptance criteria**

1. **Given** a subscription entering `past_due`,
   **when** the transition occurs,
   **then** the entity's Admins receive a notification naming the date access will stop.
2. **Given** the grace window is close to expiring,
   **when** a reminder threshold is reached,
   **then** a second notification is sent.

---

## Operability

<a id="sdo-gap-07"></a>

### SDO-GAP-07 · Celery containers report unhealthy

**As an** operator
**I want** container health to mean something for the Celery services
**so that** an orchestrator can tell a working worker from a broken one.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Severity** | Low — cosmetic today, misleading in production |
| **Diagram** | [UML 01 — deployment topology](../diagrams/uml/01-component-architecture.md) |
| **Code** | `docker-compose.yml` · `backend/Dockerfile` |
| **Linear** | [SUS-16](https://linear.app/susdevos/issue/SUS-16) · `area:bil` · `type:task` |

With the compose networking fixed, the worker and beat containers start correctly and register
all 13 tasks — but still report `unhealthy`, because they inherit a healthcheck written for the
HTTP API. A worker has no HTTP endpoint to probe.

**Acceptance criteria**

1. **Given** a running Celery worker,
   **when** its healthcheck runs,
   **then** it reports healthy — e.g. via `celery inspect ping` against that worker.
2. **Given** a worker that has lost its broker,
   **when** the healthcheck runs,
   **then** it reports unhealthy.

<a id="sdo-gap-08"></a>

### SDO-GAP-08 · Report files land in the container filesystem in development

**As a** developer
**I want** generated reports to go to MinIO like they go to S3 in production
**so that** the storage path is exercised before it reaches production.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Diagram** | [BPMN 05](../diagrams/bpmn/05-report-generation.md) |
| **Code** | `backend/tasks/reports.py` · `_upload_to_storage()` |
| **Linear** | `area:rep` · `type:task` |

`_upload_to_storage()` branches on settings and writes to `/tmp` when S3 is disabled. MinIO is
already running in compose, so the development path can exercise real object storage instead of
a branch that only exists for dev.

**Acceptance criteria**

1. **Given** the compose stack with MinIO running,
   **when** a report completes in development,
   **then** the object exists in the MinIO bucket at `node-id/entity-id/reports/uuid.fmt`.
2. **Given** the download endpoint,
   **when** called for that report,
   **then** it returns a working pre-signed URL.

<a id="sdo-gap-09"></a>

### SDO-GAP-09 · The FX fallback is never exercised

**As an** operator
**I want** confidence that the Open Exchange Rates fallback works
**so that** an ECB outage does not silently leave spend-based factors stale.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Diagram** | [UML 08 — external integrations](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/tasks/integrations/fx.py` · `sync_oer_fx_rates` |
| **Linear** | `area:ghg` · `type:task` |

`sync_ecb_fx_rates` dispatches the OER fallback via `.delay()` when the ECB source fails, and
the fallback no-ops cleanly when `OPEN_EXCHANGE_RATES_API_KEY` is unset — which it is by
default. So in practice the fallback path has never run.

**Acceptance criteria**

1. **Given** an ECB request that fails,
   **when** `sync_ecb_fx_rates` runs,
   **then** `sync_oer_fx_rates` is dispatched — asserted by a test with the ECB call patched.
2. **Given** the API key is unset,
   **when** the fallback runs,
   **then** it exits without an HTTP call and logs why.

---

## Documentation & drift

<a id="sdo-gap-10"></a>

### SDO-GAP-10 · The spec/ documents have drifted from the code

**As a** new contributor
**I want** one authoritative description of the system
**so that** I do not implement against a document that no longer matches reality.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Diagram** | [Diagram set README](../diagrams/README.md) |
| **Linear** | [SUS-17](https://linear.app/susdevos/issue/SUS-17) · `area:ten` · `type:task` |

`CLAUDE.md` already warns that a `spec/` file describing an out-of-scope feature is stale
rather than a backlog item. Deriving the diagrams confirmed the drift is wider than the
SBTi/CDP/NDC/RE100 removals — the feature-gate status code was undocumented (F5), and the
README claimed 85 tests when the suite had 199.

`spec/` remains useful as design rationale, but it is no longer a safe description of
behaviour. The diagram set and these stories are.

**Acceptance criteria**

1. **Given** each file in `spec/`,
   **when** reviewed,
   **then** it is either corrected, or marked as historical design rationale rather than
   current behaviour.
2. **Given** a reader starting from `CLAUDE.md`,
   **when** they look for current behaviour,
   **then** they are pointed at `docs/diagrams/` and `docs/stories/` first.

<a id="sdo-gap-11"></a>

### SDO-GAP-11 · Resolved — inventory verification uses dedicated authorised transitions

**As an** assurance reviewer
**I want** verifying an inventory to be an explicit action
**so that** it is auditable and permissioned in the same way as verifying a record.

| | |
|---|---|
| **Status** | ✅ Built / retired gap |
| **Diagram** | [BPMN 03](../diagrams/bpmn/03-inventory-verification.md) · [UML 07](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/emissions/views.py` · `GHGInventoriesViewSet.submit()`, `.verify()` · `backend/apps/emissions/serializers.py` · `INVENTORY_SERVER_MANAGED_FIELDS` |
| **Tests** | `backend/apps/emissions/tests/test_ghg_inventory.py` · `TestInventoryVerification` |
| **Linear** | [SUS-24 · CFI-005](https://linear.app/susdevos/issue/SUS-24/cfi-005-put-inventory-verification-behind-an-authorised-transition) · `area:inv` · `risk:security` |

This gap is retained under its stable ID for history, but its former claims are no longer true.
Normal POST/PATCH rejects status, verifier, notes, timestamps, and totals. `/submit/` performs
the Unverified → Pending transition with reconciliation and total recomputation; `/verify/` is
restricted to Entity Admin, accepts only Pending inventory, recomputes the exact boundary,
records provenance, and writes an audit event. See SDO-INV-05 and SDO-INV-14.

**Acceptance criteria**

1. **Given** an inventory in Pending,
   **when** an Entity Admin POSTs to `/ghg-inventories/{id}/verify/`,
   **then** status advances, `VerifiedBy` and `VerifiedAt` are recorded, and an audit row is written.
2. **Given** a non-admin tenant member,
   **when** they attempt the same,
   **then** the response is 403.
3. **Given** an already-verified inventory,
   **when** verification is attempted again,
   **then** it is refused with `409 invalid_transition` without altering the original verifier.
4. **Given** any normal mutation containing a verification or total field,
   **then** the serializer rejects it with HTTP 400 rather than accepting a direct state jump.

<a id="sdo-gap-12"></a>

### SDO-GAP-12 · The privilege map is rebuilt with a query per interface

**As a** user signing in
**I want** `/auth/me` to be cheap
**so that** page load does not scale with the size of the interface catalogue.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Diagram** | [UML 02 — privilege resolution](../diagrams/uml/02-domain-tenancy-rbac.md) |
| **Code** | `backend/apps/shared/permissions.py` · `build_privilege_map()` |
| **Linear** | `area:ten` · `type:performance` |

`build_privilege_map()` calls `_resolve_privilege()` once per interface, and each call issues
its own `Interfaces`, `UserPrivilegeOverrides` and `RolePrivileges` queries. With 50 seeded
interfaces that is roughly 150 queries per call, on a path hit at every sign-in and refresh.

It is correct, and small enough not to hurt yet — but it grows linearly with the catalogue,
and [SDO-GAP-01](#sdo-gap-01) would make it hotter.

**Acceptance criteria**

1. **Given** a user with roles and overrides,
   **when** `build_privilege_map()` runs,
   **then** it issues a constant number of queries regardless of interface count,
   asserted with `assertNumQueries`.
2. **Given** the same inputs,
   **when** compared against the current implementation,
   **then** the resulting map is identical — including override precedence.

<a id="sdo-gap-13"></a>

### SDO-GAP-13 · Spend-based emissions never use the FX rates that are synced daily

**As a** sustainability contributor recording a spend-based Scope 3 figure
**I want** my currency amount converted using the platform's exchange rates
**so that** spend in one currency is comparable with spend in another.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Severity** | Medium — a synced dataset with no consumer |
| **Diagram** | [UML 03 — currency](../diagrams/uml/03-domain-ghg.md) · [UML 08](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/apps/emissions/services.py` · `backend/apps/emissions/models.py:252-253` |
| **Linear** | [SUS-8](https://linear.app/susdevos/issue/SUS-8) · `area:ghg` · `type:bug` |

`tasks.integrations.sync_ecb_fx_rates` populates `ExchangeRates` every day at 17:00, and
`EmissionsData` declares `SpendAmountUSD` and `ExchangeRateToUSD`. But **`compute_emissions()`
never reads `ExchangeRates` and never writes either field** — they are reserved as
server-computed and stay `NULL` forever.

So a spend-based factor is applied to whatever currency amount the user typed, with no
normalisation. Two records in different currencies are silently incomparable.

**Acceptance criteria**

1. **Given** a spend-based record with a currency and amount,
   **when** it is saved,
   **then** `ExchangeRateToUSD` is populated from the `ExchangeRates` row effective on the
   record's date, and `SpendAmountUSD` is the converted amount.
2. **Given** no rate exists for that currency and date,
   **when** the record is saved,
   **then** the failure is explicit — the same "log loudly rather than silently pass through"
   posture `_get_gwp_factor()` already takes for a missing GWP row.
3. **Given** the rate later changes,
   **when** the record is re-saved,
   **then** the stored rate is the one effective on the record's date, not today's.

<a id="sdo-gap-14"></a>

### SDO-GAP-14 · Per-gas line-item amounts are never populated

**As an** assurance reviewer
**I want** the per-gas breakdown to carry its own computed CO₂e
**so that** I can check a record's gas-by-gas composition rather than only its total.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Severity** | Medium |
| **Diagram** | [UML 03 — inventory and records](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `EmissionsDetails` |
| **Linear** | [SUS-9](https://linear.app/susdevos/issue/SUS-9) · `area:ghg` · `type:bug` |

`EmissionsDetails` declares `EmissionsAmount` and `EmissionsAmountTonnes`, but the model has
**no `save()` override** and no service computes them — unlike `EmissionsData`, whose `save()`
calls `compute_emissions()`. The columns exist and stay `NULL`.

Only the parent record's total is authoritative today. The gas breakdown records quantities
without their CO₂e contribution.

**Acceptance criteria**

1. **Given** a detail row with a gas and amount,
   **when** it is saved,
   **then** `EmissionsAmount` and `EmissionsAmountTonnes` are computed server-side using the
   GWP for that gas from the row's `GwpDatasetId`.
2. **Given** several detail rows on one record,
   **when** their computed tonnes are summed,
   **then** the total reconciles with the parent's `EmissionsAmountTonnes` within rounding
   tolerance — or the discrepancy is surfaced rather than hidden.
3. **Given** a client submits `EmissionsAmount` on a detail row,
   **when** it is saved,
   **then** the value is overwritten, matching the rule that already governs `EmissionsData`.

<a id="sdo-gap-15"></a>

### SDO-GAP-15 · Companies House lookup is unreachable from the flow that needs it

**As a** prospect registering my organisation
**I want** my company details looked up from the register
**so that** I do not retype what Companies House already knows.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Diagram** | [BPMN 01](../diagrams/bpmn/01-tenant-onboarding.md) |
| **Code** | `backend/apps/shared/urls_integrations.py:9` · `backend/apps/users/views.py` `SignupView` |
| **Linear** | [SUS-12](https://linear.app/susdevos/issue/SUS-12) · `area:ten` · `type:feature` |

`CompaniesHouseLookupView` requires `IsAuthenticated`. `SignupView` is `AllowAny` and
`register_new_entity()` never calls it. So the integration exists but cannot be used at the one
point in the journey where it would save the most typing — an anonymous prospect gets 401.

Either the lookup should be reachable during signup (rate-limited, since it is unauthenticated
and proxies a third party), or the product should accept that enrichment happens after signup,
performed by the new Admin. Both are defensible; today's state is neither.

**Acceptance criteria**

1. **Given** a decision to support lookup at signup,
   **when** an anonymous prospect submits a company name or number,
   **then** matches are returned, under a rate limit tighter than the authenticated one.
2. **Given** a decision not to,
   **when** a newly onboarded Admin opens entity settings,
   **then** the lookup is offered there and the signup form does not imply it exists.

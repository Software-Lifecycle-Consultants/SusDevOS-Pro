# Core Feature Integrity Audit

**Status:** Active  
**Started:** 2026-08-25  
**Branch:** `codex/core-feature-integrity-audit`  
**Tracker:** [Core Feature Integrity](https://linear.app/susdevos/project/core-feature-integrity-494f51b96f1c)

## Purpose

This audit verifies that SusDevOS's core, first-party workflows are usable end to
end and preserve the meaning of the data supplied by users. It starts with user
flows, then traces critical fields through the UI, API, persistence layer,
calculation services, audit trail, and reports.

The governing integrity rule is:

> A submitted value must be persisted, deliberately transformed with traceable
> provenance, or rejected with a useful validation error. It must never be
> silently discarded.

The audit is deliberately pragmatic. It prioritises workflows required for the
current product mandate and does not turn every available model or theoretical
integration into a feature.

## Product mandate and boundaries

### In scope

- Secure organisation tenancy and role-based access.
- Projects and the phases needed to classify operational data.
- GHG inventories and Scope 1, 2, and 3 activity capture.
- Location- and market-based Scope 2 results.
- Traceable emission factors, units, GWP values, and calculations.
- Land parcels, ecosystem/species observations, removals, and restorations.
- Offsets and registry validation.
- Targets, CSV/PDF reports, and a usable audit trail.
- Marketing contact/demo capture required to support product-market discovery.

### Not in scope for this programme

- Customer API keys or public customer API access before product-market fit.
- SBTi, CDP, NDC, or RE100 integrations.
- Building UI for every junction table, tag, contact, or speculative workflow.
- Treating generated API documentation as a production product feature.

## Audit method

For every critical flow we record:

1. The user's goal and the minimum information they must supply.
2. The UI field name and the exact request payload key.
3. Serializer validation and tenant ownership checks.
4. The persisted database field and any provenance fields.
5. Each unit conversion, factor selection, GWP application, or other transform.
6. The value exposed in detail views, audit events, exports, and reports.
7. Negative tests proving unknown, unauthorised, and inconsistent input fails
   explicitly.

Derived results are server-owned. The UI should gather source observations and
show calculated results; it should not ask users to type a value that the server
will ignore and recompute from different, inaccessible child records.

## Core user-flow map

| ID | User outcome | Minimum end-to-end path | Current assessment |
|---|---|---|---|
| UF-01 | Establish an organisation and working team | Sign up -> entity -> invite/role -> authorised access | Partially usable; RBAC enforcement is tracked by SUS-5 and entity-type choices drift from the backend. |
| UF-02 | Create a project structure | Project -> phase -> assign activity/nature records | Core phase create/edit/list and emission phase selection are implemented and API-tested; bounded report proof remains. |
| UF-03 | Open a reporting inventory | Reporting period -> base year -> GWP dataset -> boundary -> save | Implemented and API/build-verified: calendar/custom period, baseline, boundary notes, consolidation approach, and active default GWP dataset persist; browser smoke remains. |
| UF-04 | Record and calculate an emission | Activity -> period -> unit -> factor -> GWP -> inventory/project/phase -> result | Source context, period, project/phase/inventory assignment, and unknown-field rejection are implemented. Canonical unit/factor semantics (SUS-20) and evidenced Scope 2 inputs (SUS-23) remain open. |
| UF-05 | Review and verify an inventory | Reconcile records -> review totals -> authorised verification/lock | Reconciliation, exact-member recomputation, submit, Entity-Admin verify, provenance, and locks are implemented and API-tested; browser smoke and production reconciliation remain. |
| UF-06 | Produce a bounded GHG report | Select inventory/year/project -> queue -> complete/fail -> download | Partially usable; the UI always sends empty parameters and failed jobs can remain queued. |
| UF-07 | Establish a nature baseline | Parcel/project -> ecosystem -> survey/species observations | Partially usable; core lists exist but record linkage/detail workflows require further lineage testing. |
| UF-08 | Record removal/restoration impacts | Project/parcel -> event -> affected species/work -> server calculation | Blocked: forms collect derived totals that are discarded and provide no way to add the child rows that drive calculation. |
| UF-09 | Record and validate offsets | Emission/project -> offset -> registry lookup -> result | Parent preservation, tenant/lock validation, and client-forgery prevention are implemented. Registry claim-depth and complete Gold Standard validation evidence remain open in SUS-32. |
| UF-10 | Capture a prospective customer request | Contact/demo form -> durable record or delivery -> explicit success/failure | Broken: no matching backend routes were found and both forms show success after failure. |

## Critical field-lineage snapshot

| Flow | User/source field | Request/API state | Persistence/transform state | Downstream consequence |
|---|---|---|---|---|
| Emission | Reporting start/end | UI sends `ReportingPeriodFrom`/`ReportingPeriodTo`; year derives from end date | Both dates and `ReportingYear` persist; inconsistent/partial periods return field-specific 400 | Period attribution now round-trips and can be checked against a formal inventory. |
| Emission | Supplier/activity context | UI sends `SupplierName` and `ActivityDescription` | Both fields persist and round-trip; obsolete `SupplierCategory`/`Remarks` inputs were removed | Material source context is retained without adding speculative fields. |
| Emission | Unit | UI sends free-text `Unit` | Calculation expects `InputUnitId` for canonical conversion | Quantity may be interpreted in the wrong unit. |
| Emission | Scope 2 factors | UI has no distinct factor inputs | Backend can accept location- and market-based values but falls back to a common result | Dual-method totals are not independently evidenced. |
| Emission | Inventory, project, phase | Selectable in create/detail UI | Same-tenant relationships persist; phase/project and inventory period/year/GWP consistency are enforced | Operational and formal-boundary attribution is explicit and testable. |
| Inventory | Reporting period and GWP dataset | Form sends explicit dates; API records the active default dataset | Required fields persist and invalid/no-default cases fail explicitly | First-party inventory creation satisfies its contract. |
| Inventory | Boundary notes | UI sends `BoundaryNotes` | `GHGInventories.BoundaryNotes` persists and round-trips | Boundary rationale remains part of the assurance record. |
| Inventory | Member records and offsets | Records carry explicit `InventoryId`; unassigned work is reconciled separately | Totals filter by exact inventory; offsets follow the immutable parent emission | Same-year inventories remain isolated and verification freezes the intended boundary. |
| Offset | Parent and registry evidence | UI supplies required `EmissionsId` plus user-declared identity fields | Parent is same-tenant and immutable; registry result fields reject client writes and reset after identity edits | Only integration-produced `valid` evidence can reduce the exact parent inventory. |
| Spend emission | Currency/local amount | Not collected by UI | Accepted fields exist; calculated FX fields are stripped but never produced | Spend-based results lack usable currency conversion (SUS-8). |
| Gas detail | Per-gas amount | Server-owned | Serializer marks it read-only; no producer computes it | Gas-level disclosure remains empty (SUS-9). |
| Removal | Total biomass carbon | UI asks the user to enter it | Serializer treats it as read-only and service derives it from child species | Input is discarded and no child-species UI exists to trigger the calculation. |
| Restoration | Estimated sequestration | UI asks the user to enter it | Serializer treats it as read-only and service derives it from restoration species | Input is discarded and calculated output remains empty. |
| Report | Project/year/inventory scope | UI always submits `Parameters: {}` | Renderers support scope parameters | Reports aggregate all available tenant data instead of the user's intended boundary. |

## Confirmed finding register

Priorities use Urgent, High, Medium, and Low. A finding is only closed when its
acceptance criteria and regression tests pass; merging code alone is not closure.

### CFI-001 — Emission capture silently discards first-party form fields

- **Priority:** High
- **Status:** Implemented and focused-suite verified on the audit branch; browser smoke pending
- **Risk:** Data loss, misleading audit trail
- **Flow:** UF-04
- **Evidence:** The emissions form submits `DateFrom`, `DateTo`, `Supplier`,
  `SupplierCategory`, and `Remarks`. `EmissionsData` instead defines
  `ReportingPeriodFrom` and `ReportingPeriodTo` and has no supplier or remarks
  fields. The mutation is assembled as an untyped object, so generated API types
  do not catch the drift.
- **Required outcome:** Decide the minimum durable provenance fields, align UI and
  API names, and reject unknown keys. Do not add fields merely because a stale UI
  happened to contain them; retain only information that supports a clear user
  or reporting need.
- **Acceptance:** A request test proves every visible field is stored or explicitly
  rejected; the detail/edit view round-trips the stored source data; an unknown
  key returns HTTP 400 with the key named.
- **Branch resolution:** The form and API now use `ReportingPeriodFrom`/
  `ReportingPeriodTo`, `SupplierName`, and `ActivityDescription`; project, phase,
  and inventory IDs round-trip; unknown keys are named in HTTP 400 responses.
- **Linear:** [SUS-21](https://linear.app/susdevos/issue/SUS-21/cfi-001-stop-silently-discarding-emission-form-fields)

### CFI-002 — Inventory creation cannot satisfy the backend contract

- **Priority:** Urgent
- **Status:** Implemented and focused-suite verified on the audit branch; browser smoke pending
- **Risk:** Core workflow unavailable, data loss
- **Flow:** UF-03
- **Evidence:** The first-party form submits reporting year, base year,
  consolidation approach, and `BoundaryNotes`. The model requires
  `ReportingPeriodFrom`, `ReportingPeriodTo`, and `GwpDatasetId`, and does not
  define `BoundaryNotes`. The view provides no defaults.
- **Required outcome:** Replace the year-only ambiguity with an explicit reporting
  period (with a convenient calendar-year choice), select or deliberately default
  the active GWP dataset, and either persist a clearly useful boundary rationale
  or remove the unsupported input.
- **Acceptance:** A user can create, reopen, and edit an inventory through the UI;
  required values and provenance persist; API and browser tests cover validation.
- **Branch resolution:** The form captures explicit/custom or calendar-year dates,
  baseline, consolidation approach, and durable boundary notes. The API records an
  active default GWP dataset and rejects invalid periods, baseline/year drift,
  unknown legacy keys, and attempts to forge server-managed fields.
- **Linear:** [SUS-19](https://linear.app/susdevos/issue/SUS-19/cfi-002-make-ghg-inventory-creation-satisfy-its-data-contract)

### CFI-003 — Emission unit/factor provenance is incomplete and may miscalculate

- **Priority:** Urgent
- **Risk:** Calculation integrity
- **Flow:** UF-04
- **Evidence:** The UI supplies a free-text unit but not `InputUnitId`. The service
  uses the selected unit's canonical conversion while factor data has a separate
  input-unit relationship that is not consistently populated. Historical seed
  data describes factors per kWh while the canonical energy unit is kJ. The
  client preview multiplies quantity by factor directly and does not reproduce
  server conversion/GWP rules.
- **Required outcome:** Define one canonical factor contract before changing
  arithmetic, reconcile seeded/imported factors and units, expose the valid unit
  choices, and make any preview use the same tested contract as the server.
- **Acceptance:** Golden fixtures cover representative Scope 1, 2, and 3 unit
  conversions; factor provenance is non-ambiguous; client and server results
  agree; incompatible units fail explicitly.
- **Linear:** [SUS-20](https://linear.app/susdevos/issue/SUS-20/cfi-003-define-and-enforce-the-canonical-emission-unitfactor-contract)

### CFI-004 — Scope 2 dual-method inputs are not usable from the UI

- **Priority:** High
- **Risk:** Calculation and reporting integrity
- **Flow:** UF-04, UF-06
- **Evidence:** The model/service supports location- and market-based emission
  factors, but the form exposes neither distinct input. Both results can therefore
  collapse to the same generic factor without evidence of the method used.
- **Required outcome:** Capture the source data needed for both methods, or label a
  method unavailable rather than presenting a fabricated dual result.
- **Acceptance:** Fixtures demonstrate independently sourced location- and
  market-based totals and report provenance; incomplete market evidence has an
  explicit status.
- **Linear:** [SUS-23](https://linear.app/susdevos/issue/SUS-23/cfi-004-capture-evidenced-scope-2-location-and-market-methods)

### CFI-005 — Inventory verification is writable by any authenticated tenant user

- **Priority:** Urgent
- **Status:** Implemented and focused-suite verified on the audit branch; browser smoke pending
- **Risk:** Assurance and audit integrity
- **Flow:** UF-05
- **Evidence:** The UI directly patches `VerificationStatus`; the inventory
  viewset uses only authentication and accepts the status in normal updates. The
  update path can assign the current user as verifier without a manager/verifier
  permission or dedicated transition rule. The UI also labels backend states
  incorrectly: it presents backend status 1 as Submitted and status 4 as
  Rejected, while the model defines them as Unverified and Verified — Third
  Party.
- **Required outcome:** Make verification state server-controlled behind a named
  permission and explicit transition endpoint. Record actor, timestamp, previous
  state, and validation failures.
- **Acceptance:** Contributor access is denied; authorised roles can perform only
  valid transitions; tests cover cross-entity, invalid-state, and audit events.
- **Branch resolution:** Normal mutation rejects verification/provenance/total
  fields. `/submit/` is the only Unverified-to-Pending path and `/verify/` is
  Pending-only and restricted to Entity Admin. Both re-run reconciliation and
  totals; verification stamps actor/time/notes and writes an audit event.
- **Linear:** [SUS-24](https://linear.app/susdevos/issue/SUS-24/cfi-005-put-inventory-verification-behind-an-authorised-transition)

### CFI-006 — Tenant-owned relationships accept foreign-entity identifiers

- **Priority:** Urgent
- **Status:** Implemented and verified on the audit branch; awaiting merge/deployment evidence
- **Risk:** Tenant isolation and aggregate corruption
- **Flow:** UF-02, UF-04, UF-08, UF-09
- **Evidence:** Emission project/phase/inventory links, removal/restoration species
  links, and offset emission links use unrestricted related-object querysets or
  lack an entity equality check. An authenticated user can submit a valid ID from
  another entity even though top-level querysets are tenant-filtered.
- **Required outcome:** Centralise tenant-owned relationship validation and apply
  it to every critical mutation, including nested actions.
- **Acceptance:** Parameterised tests prove foreign-entity IDs return HTTP 400/404
  and create no record; same-entity relations continue to work; aggregate/report
  tests cannot cross tenant boundaries.
- **Linear:** [SUS-22](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship)

### CFI-007 — Removal and restoration forms discard totals and omit calculation inputs

- **Priority:** High
- **Risk:** Data loss and calculation integrity
- **Flow:** UF-08
- **Evidence:** Forms ask users for total biomass carbon or estimated sequestration,
  but serializers mark both as read-only. Services calculate them only from
  removed/affected/restoration species child rows, for which no first-party add or
  edit workflow exists.
- **Required outcome:** Remove derived-value inputs and provide a small, guided
  child-row workflow containing only the observations required by the existing
  calculation. Include the relevant project/parcel link needed for traceability.
- **Acceptance:** A user can enter source observations, see the server-derived
  result, reopen every observation, and reproduce the result in a report; direct
  attempts to write derived values fail explicitly.
- **Linear:** [SUS-27](https://linear.app/susdevos/issue/SUS-27/cfi-007-replace-discarded-nature-totals-with-a-usable-source)

### CFI-008 — Project phases and inventory assignment are not connected end to end

- **Priority:** High
- **Status:** Implemented and focused-suite verified on the audit branch; bounded-report/browser proof pending
- **Risk:** Core workflow and reporting usability
- **Flow:** UF-02, UF-04, UF-06
- **Evidence:** Backend phase endpoints and relationships exist, but project detail
  has no phase management and emission create/detail has no phase or inventory
  selection. Phase-progress and inventory reports therefore depend on data users
  cannot create through the application.
- **Required outcome:** Add the minimal project-phase management and emission
  assignment controls; omit broader project CRM features from this programme.
- **Acceptance:** A project manager creates a phase, a sustainability manager
  assigns an emission to it and an inventory, and both bounded reports include the
  record once.
- **Branch resolution:** Project detail supports phase create/edit/list/delete with
  date validation and in-use protection. Emission create/detail supports project,
  dependent phase, and inventory selection with tenant and consistency checks.
- **Linear:** [SUS-25](https://linear.app/susdevos/issue/SUS-25/cfi-008-connect-project-phases-and-inventory-assignment-end-to-end)

### CFI-009 — Report scope is hidden and failed jobs can remain queued

- **Priority:** High
- **Risk:** Misleading output and operational usability
- **Flow:** UF-06
- **Evidence:** The report form always submits an empty parameter object although
  renderers accept project and reporting-year filters. Queue exceptions are
  caught without moving the job to a failed state.
- **Required outcome:** Expose only relevant, validated scope selectors per report
  type; persist the effective scope; transition failures to a visible terminal
  state with a safe diagnostic message.
- **Acceptance:** Project/inventory/year isolation is tested; the downloaded report
  displays its boundary; success and failure jobs both reach terminal states.
- **Linear:** [SUS-26](https://linear.app/susdevos/issue/SUS-26/cfi-009-make-reports-bounded-and-jobs-terminal)

### CFI-010 — Contact and demo forms falsely confirm lost submissions

- **Priority:** High
- **Risk:** Product-market discovery and user trust
- **Flow:** UF-10
- **Evidence:** No matching backend routes were found for `/api/public/contact/`
  or `/api/public/demo-request/`. Both frontend forms show a success state after
  non-success responses or network errors.
- **Required outcome:** Use one durable, monitored delivery mechanism with abuse
  controls, or temporarily replace the forms with an honest contact method.
- **Acceptance:** A successful submission has a durable receipt/delivery ID;
  failures remain visible and retryable; integration tests exercise both paths.
- **Linear:** [SUS-28](https://linear.app/susdevos/issue/SUS-28/cfi-010-stop-falsely-confirming-lost-contact-and-demo-requests)

### CFI-011 — Entity settings offers values rejected by the backend

- **Priority:** Medium
- **Risk:** Usability and contract drift
- **Flow:** UF-01
- **Evidence:** The settings UI offers entity types 9–12 while the model accepts
  only 1–8.
- **Required outcome:** Source choices from the API contract or a shared generated
  enum and remove unsupported values until the business model defines them.
- **Acceptance:** Every selectable value saves successfully; an API contract test
  prevents frontend/backend choice drift.
- **Linear:** [SUS-29](https://linear.app/susdevos/issue/SUS-29/cfi-011-share-valid-entity-type-choices-across-ui-and-api)

### CFI-012 — Critical create paths bypass the audit logging mixin

- **Priority:** High
- **Risk:** Audit integrity
- **Flow:** UF-04, UF-09
- **Evidence:** emission-data and offset viewsets override `perform_create` and call
  `serializer.save()` directly rather than the audit mixin helper used elsewhere.
- **Required outcome:** Make audit recording unavoidable for critical mutations
  and ensure the audit event records actor, entity, object, action, and material
  before/after values without leaking secrets.
- **Acceptance:** Create/update/delete and assurance transitions produce exactly
  one expected audit event; rollback tests prove no event survives a failed
  transaction.
- **Linear:** [SUS-30](https://linear.app/susdevos/issue/SUS-30/cfi-012-make-audit-events-unavoidable-for-critical-mutations)

### CFI-013 — Standalone offset creation discards its parent emission

- **Priority:** High
- **Status:** API and production-build verified; interactive browser smoke pending
- **Risk:** Data loss, tenant isolation, core workflow unavailable
- **Flow:** UF-09
- **Evidence:** The offsets page submits `EmissionsId` to the standalone endpoint,
  but `EmissionsOffsetsSerializer` marks it read-only and the view only supplies
  entity/creator fields. The submitted relationship is discarded and the
  non-null model relationship cannot be satisfied. Simply making it writable
  without an ownership check would introduce a cross-tenant write vector.
- **Required outcome:** Require a same-tenant parent on standalone create, keep
  nested create bound to its URL parent, honour verified-parent locks, and keep
  registry-derived validation fields server-owned.
- **Acceptance:** Both create routes are tested; missing/foreign/locked parents
  fail explicitly and write nothing; same-tenant selection persists and
  round-trips.
- **Branch resolution:** Standalone create requires and persists a same-tenant
  `EmissionsId`; nested create remains URL-bound; both respect record/inventory
  locks and prevent offset reparenting.
- **Linear:** [SUS-31](https://linear.app/susdevos/issue/SUS-31/cfi-013-make-standalone-offset-creation-preserve-its-parent-emission)

### CFI-014 — Clients can self-assert carbon-offset registry validity

- **Priority:** Urgent
- **Status:** Direct client forgery is blocked; registry claim-depth review remains open
- **Risk:** Calculation and assurance integrity
- **Flow:** UF-09, UF-06
- **Evidence:** The offset serializer allows authenticated clients to write
  registry validation status, timestamp, project metadata, vintage, and
  beneficiary. Inventory net totals deduct offsets whose status is `valid`, so
  a caller can currently assert the condition that makes its credit reduce
  reported emissions.
- **Required outcome:** Keep user-declared certificate/reference inputs separate
  from registry-derived evidence; make result fields server-owned and permit
  status transitions only through the explicit validation service.
- **Acceptance:** Forged create/PATCH values cannot alter registry results; new
  credits begin unverified; only a tested validation transition can mark them
  valid/invalid; inventory totals deduct only service-validated credits.
- **Branch resolution:** All registry result fields reject API input. New claims
  start unverified, and any identity change clears prior validation evidence.
  Verra positive validation remains tested; Gold Standard and the sufficiency of
  evidence for the full credit/retirement claim remain open.
- **Linear:** [SUS-32](https://linear.app/susdevos/issue/SUS-32/cfi-014-prevent-clients-from-self-validating-carbon-offsets)

### CFI-015 — Formal inventory totals ignore explicit inventory membership

- **Priority:** Urgent
- **Status:** Runtime implementation and focused-suite verified; production dry-run reconciliation/backfill pending
- **Risk:** Calculation, boundary, and assurance integrity
- **Flow:** UF-04, UF-05, UF-06
- **Evidence:** `_compute_inventory_totals()` filters emissions by entity and
  `ReportingYear`, not by `InventoryId` or the inventory period. It therefore
  includes unassigned records and records assigned to another same-year
  inventory. Offsets are selected through their parent emission's year rather
  than its inventory membership.
- **Required outcome:** Make explicit inventory membership authoritative, expose
  assignment and unassigned-record reconciliation, validate period/entity
  consistency, and provide a dry-run production reconciliation before any
  backfill.
- **Acceptance:** Two same-year inventory fixtures remain isolated; unassigned
  records are visible but excluded; offsets follow their parent inventory;
  period mismatches fail; verification recomputes the exact member boundary.
- **Branch resolution:** `_compute_inventory_totals()` filters on the exact
  `InventoryId`; offsets follow the parent emission's membership; the UI/API expose
  unassigned candidates and incomplete-period records; submit/verify recompute the
  exact boundary and require explicit review acknowledgement.
- **Linear:** [SUS-33](https://linear.app/susdevos/issue/SUS-33/cfi-015-compute-formal-inventory-totals-from-explicit-inventory)

## Existing backlog items retained rather than duplicated

| Linear | Existing concern | Relationship to this audit |
|---|---|---|
| SUS-5 | RBAC exists but is not enforced | Dependency for UF-01 and CFI-005; verification still needs its own transition rules. |
| SUS-8 | Spend currency/FX fields are stripped but never calculated | Required part of the GHG lineage closure. |
| SUS-9 | Per-gas detail amounts are never computed | Required part of the GHG lineage closure. |
| SUS-10 | Scope 3 relevance assessment lacks an API | Assess after the primary capture/inventory path works. |
| SUS-11 | Threatened-species flag is not implemented | Required for complete nature-risk reporting, after source observations are usable. |
| SUS-14 | Inventory self-verification policy is undecided | Product-policy dependency for CFI-005; it does not justify unrestricted writes. |
| SUS-17 | Documentation status has drifted | This audit document becomes the evidence source for core-flow status. |

## Execution order

### Batch 1 — Stop corruption and unblock the GHG backbone

1. CFI-006 tenant-owned relationship validation.
2. CFI-014 server-owned offset validation state.
3. CFI-002 usable inventory creation.
4. CFI-001 honest, round-trippable emission capture.
5. CFI-008 inventory assignment controls needed by the backbone.
6. CFI-015 membership-based totals and reconciliation.
7. CFI-005 controlled inventory verification.

### Batch 2 — Establish calculation truth

1. CFI-003 canonical unit/factor contract and reconciliation fixtures.
2. CFI-004 Scope 2 dual-method provenance.
3. SUS-8 spend/FX production.
4. SUS-9 per-gas detail production.

### Batch 3 — Complete first-party operational flows

1. CFI-008 project phase and inventory assignment.
2. CFI-007 removal/restoration source-observation workflow.
3. CFI-013 usable standalone offset creation.
4. CFI-009 bounded, terminal reports.
5. CFI-012 complete audit events.

### Batch 4 — Product usability and release proof

1. CFI-010 honest lead capture.
2. CFI-011 shared entity-type choices.
3. SUS-10 and SUS-11 after their source workflows are sound.
4. Cross-flow browser, API, tenant-isolation, calculation-fixture, report, and
   deployment smoke tests.

## Closure gate

A finding may be marked complete only when:

- Its accepted user flow works in the first-party UI and API.
- Every visible input round-trips or receives explicit validation.
- All tenant-owned relationships are ownership-checked.
- Calculation fixtures document units, factors, GWP source, rounding, and expected
  result.
- Audit events and reports show the same effective boundary and provenance.
- Automated regression tests cover success, invalid input, and unauthorised input.
- Documentation and the corresponding Linear issue link to the verification
  evidence.

## Verification log

| Date | Batch | Evidence | Result |
|---|---|---|---|
| 2026-08-25 | Relationship and offset hardening | 19 new create/PATCH API regressions; complete backend suite; frontend type-check and production build; Ruff on changed backend files | 243/243 backend tests passed; 51/51 frontend routes built; changed-file Ruff clean. CFI-006 is implementation-complete. CFI-013 awaits an interactive form smoke. CFI-014 remains open because registry tasks still need proof that their evidence supports the full credit claim, not merely a matching project/serial. |
| 2026-08-26 | GHG capture, inventory boundary, phase assignment, reconciliation, and assurance transition | 81 focused backend regressions across emissions/inventory/projects/restorations; frontend TypeScript check; canonical user stories and 58 Mermaid definitions synchronised with bidirectional Linear traceability | Focused tests and type-check passed. CFI-001, CFI-002, CFI-005, CFI-008, and the runtime part of CFI-015 are ready for review. Full-suite/build, browser smoke, and SUS-33 production dry-run remain closure gates. |

## Decisions still required

These decisions are intentionally narrow and should be resolved inside their
implementation tickets:

- The canonical denominator contract for emission factors and migration strategy
  for factors whose current unit is missing or inconsistent.
- Whether self-verification is permitted by product policy — a verifier signing off an
  inventory whose records they entered themselves. Partly settled: verification now requires
  Manager and above, so Staff who enter figures cannot sign them off. What remains open is
  whether a Manager may verify their own work (tracked as SDO-GAP-03 / SUS-14), and the
  evidence/actor model required before third-party assurance status can be exposed.
- The durable delivery mechanism for contact/demo requests.

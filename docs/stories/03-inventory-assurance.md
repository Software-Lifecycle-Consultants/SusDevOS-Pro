# 03 — Inventory & Assurance

Formal GHG inventories: opening a reporting year, assessing Scope 3 relevance, assigning
records, computing totals, and the verification/immutability/unlock chain that makes an
inventory defensible to an assurance provider. IDs `SDO-INV-*`.

Three of these stories exist because of review findings — F3 (double-verification), F9
(unlock guard), F10 (verify was open to anyone) — and are marked accordingly. Two stories
(Scope 3 relevance assessment, threatened-species-equivalent gaps in this epic) describe
model-only scaffolding with no API surface; they are recorded as ⬜ Gap rather than padded
into a Built story.

---

### SDO-INV-01 · Open an annual GHG inventory choosing a GWP dataset and consolidation approach

**As a** sustainability lead
**I want** to open a formal inventory for a reporting year with a chosen GWP dataset and
consolidation approach
**so that** all emissions recorded against it use a consistent basis for the year.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above (no Manager-level gate on creation) |
| **Diagram** | [BPMN 03 §Annual inventory process](../diagrams/bpmn/03-inventory-verification.md) · [UML 03 §Inventory and emissions records](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `GHGInventories` · `backend/apps/emissions/views.py` · `GHGInventoriesViewSet` |
| **Tests** | `backend/apps/emissions/tests/test_ghg_inventory.py` (`TestInventoryCreate`, `TestInventoryFeatureGate`) |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** an authenticated user whose entity has the `ghg_inventory_formal` feature
   enabled, **when** they `POST /api/ghg-inventories/` with `ReportingYear`,
   `ReportingPeriodFrom`/`ReportingPeriodTo`, `GwpDatasetId` and `ConsolidationApproach`
   (1 Equity Share / 2 Financial Control / 3 Operational Control),
   **then** the response is `201` with `VerificationStatus == 1` (Unverified) and `EntityId`
   set from `request.entity_id`, never from the request body.
2. **Given** an entity without the `ghg_inventory_formal` feature, **when** it `GET`s or
   `POST`s `/api/ghg-inventories/`, **then** the response is `402` with
   `code == "feature_gated"` and `feature == "ghg_inventory_formal"`.
3. **Given** a SuperAdmin user, **when** they access `/api/ghg-inventories/` on any entity,
   **then** the feature gate is bypassed (`test_superadmin_bypasses_feature_gate`).

---

### SDO-INV-02 · Assess Scope 3 category relevance with a mandatory exclusion justification

**As a** sustainability lead
**I want** to mark each of the 15 Scope 3 categories relevant or not, with a mandatory
reason when excluded
**so that** an omitted category is a documented decision, not a silent gap in the inventory.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Role** | Manager (per BPMN 03; unenforceable today — no endpoint exists) |
| **Diagram** | [BPMN 03 §Scope 3 relevance assessment](../diagrams/bpmn/03-inventory-verification.md) · [UML 03 §Inventory and emissions records](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `Scope3RelevanceAssessments` (model + admin registration only) |
| **Tests** | none |
| **Linear** | [SUS-10](https://linear.app/susdevos/issue/SUS-10) · `area:inv` · `type:feature` |

**Acceptance criteria (target behaviour — not yet buildable against a real endpoint)**

1. **Given** the model `Scope3RelevanceAssessments` (`CategoryNumber` 1–15, `IsRelevant`,
   `ExclusionReason`, unique constraint on `(InventoryId, CategoryNumber)`), **when** the
   `apps/emissions` serializers and views are inspected, **then** no
   `Scope3RelevanceAssessmentsSerializer` and no viewset or nested action exists anywhere in
   `apps/emissions/serializers.py` or `apps/emissions/views.py` — there is currently no way
   to create or read a relevance assessment through the API.
2. **Given** `ExclusionReason` exists as a plain nullable `TextField` with no serializer to
   enforce it, **when** a category is marked `IsRelevant=False`, **then** nothing today makes
   the justification mandatory — the "MANDATORY justification" behaviour shown in BPMN 03 is
   documentation of intent, not implemented validation.
3. **To close this gap:** add `GET/POST /api/ghg-inventories/{id}/scope3-assessments/`
   (mirroring the existing nested `/milestones/` action on `TargetsViewSet`) with
   serializer-level validation requiring `ExclusionReason` when `IsRelevant` is `False`.

---

### SDO-INV-03 · Assign emissions records to an inventory

**As a** contributor
**I want** to attach an emissions record to a specific GHG inventory
**so that** it counts toward that reporting year's totals and inherits the inventory's lock
once verified.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 03 §Inventory and emissions records](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `EmissionsData.InventoryId` (FK, `SET_NULL`) · `backend/apps/emissions/views.py` · `EmissionsDataViewSet._inventory_locked_response()` |
| **Tests** | `backend/apps/emissions/tests/test_verified_immutability.py` (`TestVerifiedInventoryChildRows`) |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** `InventoryId` is supplied on `POST /api/emissions/` and the referenced
   inventory has `VerificationStatus < 3`, **when** the record is created,
   **then** the response is `201` and the record is linked
   (`test_add_row_to_unverified_inventory_is_allowed`).
2. **Given** the referenced inventory has `VerificationStatus >= 3`, **when** the same
   `POST` is made, **then** the response is `403` with `code == "verified_immutable"` and no
   record is created (`test_add_row_to_verified_inventory_returns_403`).
3. **Given** an existing, still-editable record with no inventory, **when** it is `PATCH`ed
   with `InventoryId` pointing at a *verified* inventory, **then** the response is `403` —
   closing the bypass where `create()` checked the target inventory but a re-point via
   `update()` did not (`test_reassign_row_into_verified_inventory_returns_403`).

---

### SDO-INV-04 · Inventory scope totals are recomputed nightly

**As a** sustainability lead
**I want** an inventory's Scope 1/2/3 totals to stay current without manual recalculation
**so that** the figures I review always reflect the latest recorded emissions.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | System (Celery, 01:00 daily) |
| **Diagram** | [BPMN 03 §Annual inventory process (L4)](../diagrams/bpmn/03-inventory-verification.md) |
| **Code** | `backend/tasks/emissions.py` · `recompute_stale_inventory_totals()`, `_compute_inventory_totals()` |
| **Tests** | `backend/apps/emissions/tests/test_offset_validation.py` (calls `_compute_inventory_totals()` directly) |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** `EmissionsData` rows for an entity + `ReportingYear` with `Status < 4`,
   **when** `_compute_inventory_totals(inventory)` runs, **then** `TotalScope1Tonnes`,
   `TotalScope2LocationTonnes`/`TotalScope2MarketTonnes`, and `TotalScope3Tonnes` are the
   summed `EmissionsAmountTonnes` (Scope 2 from `EmissionsAmountLocationBased`/
   `MarketBased` ÷ 1000).
2. **Given** offsets scoped to the inventory's `ReportingYear` via their linked
   `EmissionsId`, **when** totals are recomputed, **then** only
   `RegistryValidationStatus == "valid"` offsets are summed into `TotalOffsetsTonnes` and
   subtracted into `NetEmissionsTonnes` — `unverified`/`pending`/`invalid` offsets, and valid
   offsets from a *different* reporting year, are excluded
   (`test_only_valid_offsets_reduce_net_total`, `test_valid_offset_in_other_year_does_not_reduce_this_years_net`).
3. **Given** `recompute_stale_inventory_totals()` selects inventories where
   `TotalsLastComputedAt` is `NULL` or older than 24h and `VerificationStatus < 3`,
   **then** verified inventories are never touched by the nightly sweep.

*Note: only `_compute_inventory_totals()` — the totals formula — is directly tested. The
staleness-selection query and the scheduled task itself (`recompute_stale_inventory_totals`,
01:00 daily) have no test exercising them end to end.*

---

### SDO-INV-05 · Submit an inventory for verification

**As a** sustainability lead
**I want** to move an inventory from Unverified to Pending
**so that** a verifier knows it is ready for review.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above — **no** `IsManagerOrAbove` gate on this transition |
| **Diagram** | [UML 07 §7.1 GHG inventory verification](../diagrams/uml/07-state-machines.md) · [BPMN 03](../diagrams/bpmn/03-inventory-verification.md) |
| **Code** | `backend/apps/emissions/views.py` · `GHGInventoriesViewSet` (no dedicated `/submit/` action) |
| **Tests** | `backend/apps/emissions/tests/test_ghg_inventory.py` (`TestInventoryEdit` — edits while unverified only) |
| **Linear** | `area:inv` · `type:spec` · `risk:security` |

**Acceptance criteria**

1. **Given** an inventory at `VerificationStatus == 1`, **when** a client `PATCH`es
   `/api/ghg-inventories/{id}/` with `{"VerificationStatus": 2}`, **then** the response is
   `200` and the inventory remains editable — `2` is below the `>= 3` lock threshold in
   `_check_not_verified()`.
2. **Given** `VerificationStatus` is not in `GHGInventoriesSerializer.read_only_fields`,
   **when** *any* authenticated tenant member (not only Manager+) submits this `PATCH`,
   **then** the request succeeds — unlike `EmissionsData.verify()` (F10), there is no
   `IsManagerOrAbove` restriction on `GHGInventoriesViewSet`'s update path.
3. **Given** the same or a later `PATCH` advances `VerificationStatus` to `>= 3`,
   **when** `perform_update()` runs, **then** `VerifiedBy`/`VerifiedAt` are stamped only at
   that transition, not at the Pending (2) step.

*Note: no test currently exercises the `VerificationStatus == 2` transition specifically —
existing tests jump directly from 1 to 3 (`test_verify_stamps_verifier_identity`).*

---

### SDO-INV-06 · Verify an individual emissions record — Manager and above only

**As a** Manager
**I want** verification of an emissions record restricted to Manager-or-above
**so that** the record's own creator cannot self-attest it as reviewed.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Manager and above (`IsManagerOrAbove`) |
| **Diagram** | [UML 07 §7.2 Emissions record verification](../diagrams/uml/07-state-machines.md) · [UML 06 §6.3](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet.get_permissions()`, `.verify()` · `backend/apps/emissions/services.py` · `verify_record()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py` (`TestVerifyPermission`) |
| **Linear** | `area:inv` · `type:spec` · `risk:security` |

**Acceptance criteria**

1. **Given** a `staff`-role user (below `IsManagerOrAbove`), **when** they
   `POST /api/emissions/{id}/verify/` — including on a record they created themselves,
   **then** the response is `403` (`test_staff_cannot_verify`).
2. **Given** a Manager-or-above user, **when** they `POST /api/emissions/{id}/verify/` with
   `{"notes": "..."}`, **then** the response is `204` and a subsequent `GET` shows
   `VerificationStatus == 3` (`test_manager_or_admin_can_still_verify`).
3. This restriction was added after finding **F10** showed `verify` open to any
   authenticated user, including the record's own creator, defeating segregation of duties —
   see [F10](../diagrams/FINDINGS.md#f10).

---

### SDO-INV-07 · A record cannot be verified twice, and a second attempt cannot overwrite the original verifier

**As a** compliance owner
**I want** a second verification attempt rejected outright
**so that** the original verifier's attestation can never be silently replaced.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Manager and above |
| **Diagram** | [UML 07 §7.2](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/emissions/services.py` · `verify_record()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py` (`test_double_verify_returns_400`, `test_verify_record_service_rejects_double_verification`) |
| **Linear** | `area:inv` · `type:spec` · `risk:security` |

**Acceptance criteria**

1. **Given** a record already at `VerificationStatus >= 3`, **when**
   `POST /api/emissions/{id}/verify/` is called again, **then** the response is `400` with
   `code == "already_verified"`.
2. **Given** a *direct* second call to `verify_record()` — not via the view (a management
   command, a retried task) — **when** `VerificationStatus >= 3`, **then** it raises
   `ValidationError({"code": "already_verified"})` rather than silently succeeding, so every
   call site inherits the guard, not only the viewset.
3. **Given** a rejected second attempt, **when** the record is re-read, **then**
   `VerifiedBy` and `VerifiedAt` are unchanged from the first, successful verification.

Link: [F3](../diagrams/FINDINGS.md#f3).

---

### SDO-INV-08 · Verified records and inventories are immutable — PATCH/DELETE return 403

**As a** compliance owner
**I want** every write path to a verified row and its line items blocked
**so that** an audit-locked figure can never be quietly changed.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above (all writers are blocked equally; only SuperAdmin unlock bypasses it — see SDO-INV-09) |
| **Diagram** | [UML 07 §7.1 / §7.2](../diagrams/uml/07-state-machines.md) · [BPMN 03](../diagrams/bpmn/03-inventory-verification.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet.update()`/`.destroy()`, `GHGInventoriesViewSet._check_not_verified()` |
| **Tests** | `backend/apps/emissions/tests/test_verified_immutability.py`, `backend/apps/emissions/tests/test_ghg_inventory.py` (`TestInventoryVerification`) |
| **Linear** | `area:inv` · `type:spec` · `risk:security` |

**Acceptance criteria**

1. **Given** an `EmissionsData` record at `VerificationStatus >= 3`, **when** `PATCH` or
   `DELETE /api/emissions/{id}/` is called, **then** the response is `403` with
   `code == "verified_immutable"` (`test_patch_verified_record_returns_403`,
   `test_delete_verified_record_returns_403`).
2. **Given** a `GHGInventories` row at `VerificationStatus >= 3`, **when** `PATCH` or
   `DELETE /api/ghg-inventories/{id}/` is called, **then** the response is `403` with the
   same code (`test_patch_verified_inventory_returns_403`,
   `test_delete_verified_inventory_returns_403`).
3. **Given** a record whose *parent inventory* is verified but the record itself was never
   individually verified, **when** its detail/offset line items are added, edited or deleted
   — nested, or via the standalone `/api/emissions-offsets/` endpoint — **then** the
   response is still `403`; the inventory lock cascades to member rows and their line items
   (`test_nested_add_detail_to_row_in_verified_inventory_returns_403`,
   `test_standalone_patch_offset_in_verified_inventory_returns_403`).

---

### SDO-INV-09 · A SuperAdmin can unlock a verified record with a mandatory reason, writing a 7-year-retention audit entry

**As a** SuperAdmin
**I want** to unlock a verified record only with a stated reason
**so that** a correction is possible without breaking audit traceability.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | SuperAdmin only |
| **Diagram** | [UML 07 §7.2](../diagrams/uml/07-state-machines.md) · [UML 06 §6.3](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/services.py` · `unlock_record()` · `backend/apps/emissions/views.py` · `EmissionsDataViewSet.unlock()`, `GHGInventoriesViewSet.unlock()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py` (`TestUnlock`), `backend/apps/emissions/tests/test_ghg_inventory.py` (`TestInventoryUnlock`) |
| **Linear** | `area:inv` · `type:spec` · `risk:security` |

**Acceptance criteria**

1. **Given** a non-SuperAdmin user, **when** they `POST /api/emissions/{id}/unlock/` or
   `/api/ghg-inventories/{id}/unlock/`, **then** the response is `403`
   (`test_unlock_requires_superadmin`, `test_non_sa_cannot_unlock`).
2. **Given** a SuperAdmin with no `reason` in the body, **when** they call either `/unlock/`
   action, **then** the response is `400` with `code == "reason_required"`
   (`test_unlock_requires_reason`).
3. **Given** a SuperAdmin with a reason, **when** they unlock a verified emissions record,
   **then** `VerificationStatus` resets to `1`, an `AuditLog` row is written with
   `Action == "Unlock_Verified"`, `TableName == "emissions_data"`, `RetentionTier == 3`
   (7-year retention), and the record becomes editable again
   (`test_unlock_writes_audit_log`, `test_sa_can_unlock_with_reason`).
4. **Given** `unlock_record()` is called directly with a non-SuperAdmin `unlocked_by`,
   **when** it runs, **then** it raises `PermissionDenied` *before* any mutation or audit
   write — no `Unlock_Verified` row is created for the rejected attempt
   (`test_unlock_record_service_denies_non_superadmin`).

Link: [F9](../diagrams/FINDINGS.md#f9).

---

### SDO-INV-10 · First-party versus third-party assurance status

**As a** verifier
**I want** to record whether verification was internal sign-off or external assurance
**so that** the inventory's provenance is distinguishable in reporting.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above (no role distinction between who may set 3 vs 4) |
| **Diagram** | [UML 07 §7.1](../diagrams/uml/07-state-machines.md) · [BPMN 03 §L6](../diagrams/bpmn/03-inventory-verification.md) |
| **Code** | `backend/apps/emissions/models.py` · `GHGInventories.VERIFICATION_STATUS_CHOICES` (3 = Verified - First Party, 4 = Verified - Third Party) |
| **Tests** | none distinguish 3 from 4 |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** `VerificationStatus` choices include `3` ("Verified - First Party") and `4`
   ("Verified - Third Party"), **when** either value is `PATCH`ed onto an inventory,
   **then** both satisfy the same `>= 3` immutability comparison identically — a single
   guard locks both states (UML 07 §7.1's note: "adding a state 5 would automatically
   inherit immutability").
2. **Given** no dedicated "assurance type" selector or workflow exists, **when** a client
   chooses between first-party and third-party, **then** the choice is made purely by which
   numeric value the `PATCH` body sets — there is no server-side restriction on *who* may set
   `4` versus `3` (both are reachable by any authenticated tenant member, per SDO-INV-05).
3. **Given** `Pending → VerifiedThird` is a legal direct transition in UML 07 §7.1, **when**
   an inventory jumps straight from `2` to `4` without ever passing through `3`, **then**
   nothing in the code prevents it — the state machine diagram documents this as legal, but
   no test exercises it.

*Note: no test asserts a transition specifically to `VerificationStatus == 4`, or that
`VerifiedBy`/`VerifiedAt` are stamped the same way for third-party as for first-party.*

---

### SDO-INV-11 · Consolidated group emissions across an entity hierarchy

**As a** group sustainability lead
**I want** consolidated Scope 1/2/3 totals across an entity and its subsidiaries
**so that** I can report at the group level under the chosen consolidation approach.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [BPMN 03 §Multi-entity consolidation](../diagrams/bpmn/03-inventory-verification.md) |
| **Code** | `backend/apps/entities/services.py` · `compute_consolidated_emissions()`, `_entity_scope_totals()` · `backend/apps/entities/views.py` · `EntitiesViewSet.consolidated_emissions()` |
| **Tests** | none |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** a parent entity with subsidiaries linked via `Entities.ParentEntityId`,
   **when** `GET /api/entities/{id}/consolidated-emissions/?year=YYYY` is called, **then**
   the response includes `own_emissions`, one `subsidiaries[]` entry per active child with
   `standalone` and `attributed` totals, and a `consolidated_totals` sum.
2. **Given** `approach=1` (Equity Share), **when** a subsidiary's totals are attributed,
   **then** each scope is multiplied by `OwnershipSharePercent / 100`; **given**
   `approach=2` or `3` (Financial/Operational Control), **then** the subsidiary is
   attributed at 100% (`share = Decimal("1")`).
3. **Given** no `approach` query param is supplied, **when** the endpoint runs, **then** it
   defaults to `entity.ConsolidationApproach`, falling back to `3` (Operational Control) if
   unset — note this is the *entity's* stored approach, distinct from the *inventory's* own
   `ConsolidationApproach` used by `_compute_inventory_totals()`.

*Note: `compute_consolidated_emissions()` and the `consolidated-emissions` action have no
test file under `backend/apps/entities/tests/`.*

---

### SDO-INV-12 · Set a reduction target with milestones

**As a** sustainability lead
**I want** to define a generic reduction target with year-by-year milestones
**so that** progress can be tracked against a baseline.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 03 §Targets](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `Targets`, `TargetMilestones` · `backend/apps/emissions/views.py` · `TargetsViewSet.milestones()` |
| **Tests** | none |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** an authenticated tenant member, **when** they `POST /api/targets/` with
   `TargetName`, `TargetType`, `BaselineYear`, `TargetYear`, `ReductionPercent`, **then**
   the response is `201` with `EntityId` set from `request.entity_id`. Per CLAUDE.md, there
   is deliberately no SBTi target-validation call anywhere in this path.
2. **Given** a `Targets` row, **when** they `POST /api/targets/{id}/milestones/` with
   `MilestoneYear` and `TargetEmissionsTonnes`, **then** the response is `201` and the
   milestone is linked via `TargetId` (FK `CASCADE`).
3. **Given** `ValidationStatus` on `Targets` defaults to `1` with no `choices` and no
   registry-sync task referencing it, **then** it functions as a free-form internal review
   flag only, not an external submission/registry state.

*Note: no test file covers `Targets` or `TargetMilestones` create/list at any layer — this
story is transcribable into tests but currently unverified.*

---

### SDO-INV-13 · Milestone actuals are linked from recorded emissions nightly

**As a** sustainability lead
**I want** each milestone's actual emissions populated automatically once its year has passed
**so that** I can see target-vs-actual without manual data entry.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | System (Celery, 01:30 daily) |
| **Diagram** | [UML 03 §Targets](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/tasks/emissions.py` · `link_milestone_actuals()` |
| **Tests** | none |
| **Linear** | `area:inv` · `type:spec` |

**Acceptance criteria**

1. **Given** a `TargetMilestone` whose `MilestoneYear` has passed and
   `ActualEmissionsTonnes` is still `NULL`, **when** `link_milestone_actuals()` runs,
   **then** it finds the matching `GHGInventories` row (same `EntityId`,
   `ReportingYear == MilestoneYear`, `NetEmissionsTonnes` not null) and sets
   `ActualEmissionsTonnes` to that inventory's `NetEmissionsTonnes`.
2. **Given** `TargetEmissionsTonnes` is checked with `is not None` rather than truthiness
   — a net-zero milestone has `TargetEmissionsTonnes == 0`, which is falsy — **when**
   `actual <= target`, **then** `IsAchieved` is set `True` even for a zero target.
3. **Given** no matching `GHGInventories` row exists for that entity + year, **when** the
   task runs, **then** the milestone is left untouched (`ActualEmissionsTonnes` stays
   `NULL`) and is reconsidered on the next nightly run.

*Note: `link_milestone_actuals` (scheduled 01:30 daily) has no test of its own anywhere in
the test suite — the behaviour above is read directly from the task body.*

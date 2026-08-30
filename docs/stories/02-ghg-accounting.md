# Epic 02 — GHG accounting

`SDO-GHG-*` — activity data capture, server-side calculation, factors, GWP.

Primary diagrams: [UML 03](../diagrams/uml/03-domain-ghg.md) ·
[UML 06 §6.2](../diagrams/uml/06-sequences.md) ·
[BPMN 02](../diagrams/bpmn/02-emissions-lifecycle.md).

The core formula: `kg CO2e = quantity × emission_factor × GWP100`, `tonnes = kg / 1000`.

---

<a id="sdo-ghg-01"></a>

### SDO-GHG-01 · Record a Scope 1 emission from activity data

**As a** sustainability contributor
**I want** to enter a Scope 1 activity record (fuel, quantity, emission factor)
**so that** it becomes part of the entity's GHG accounting.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 — Main process](../diagrams/bpmn/02-emissions-lifecycle.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet.create()` · `backend/apps/emissions/models.py` · `EmissionsData` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestGHGCalculation::test_scope1_co2_calculation` |
| **Linear** | [SUS-21 · CFI-001](https://linear.app/susdevos/issue/SUS-21/cfi-001-stop-silently-discarding-emission-form-fields) · `area:ghg` · `risk:data-loss` |

**Acceptance criteria**

1. **Given** a valid `POST /api/emissions/` body with `Scope=1`, `QuantityOrCost="1000.0000"`, `EmissionFactor="2.63900000"` (DEFRA 2024 diesel), `Gas="CO2"`, and a `GwpDatasetId`,
   **when** the record is created,
   **then** the response is `201` and `EmissionsAmount == "2639.0000"`, `EmissionsAmountTonnes == "2.639000"` (`test_scope1_co2_calculation`).
2. **Given** no `GwpDatasetId` is supplied in the payload,
   **when** `EmissionsDataViewSet.perform_create()` runs,
   **then** it defaults to `GwpDatasets.objects.filter(IsDefault=True).first()` — **this fallback has no dedicated test**; every existing test supplies `GwpDatasetId` explicitly via the `gwp_dataset` fixture.

---

### SDO-GHG-02 · The server computes the emission; client-sent EmissionsAmount is always overwritten

**As a** sustainability contributor
**I want** the platform to calculate emissions from my activity data
**so that** the figure is defensible and consistent regardless of what my client sent.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 06 §6.2 — Emissions record creation and server-side calculation](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/services.py` · `compute_emissions()` · `backend/apps/emissions/models.py` · `EmissionsData.save()` · `backend/apps/emissions/serializers.py` · `CALCULATED_FIELDS` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestGHGCalculation::test_client_submitted_amount_is_overwritten` |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** a record submitted with `EmissionsAmount="9999999.0000"` and `EmissionsAmountTonnes="9999.000000"` set by the client,
   **when** it is saved,
   **then** both values are overwritten by the server-computed figures (`2639.0000` / `2.639000` for the same inputs as SDO-GHG-01) — enforced twice: `EmissionsDataSerializer.validate()` pops every `CALCULATED_FIELDS` key from client input *before* validation, and `EmissionsData.save()` calls `compute_emissions(self)` before `super().save()` regardless (`test_client_submitted_amount_is_overwritten`).
2. **Given** `EmissionsData.save()` is called directly (not through the API — e.g. a management command or bulk-recalculation task),
   **when** it runs,
   **then** the same `compute_emissions()` call fires, so the overwrite guarantee holds for every call site, not just the DRF serializer path.

---

<a id="sdo-ghg-03"></a>

### SDO-GHG-03 · Input quantities are converted to a canonical unit before calculation

**As a** sustainability contributor
**I want** to enter activity data in whatever unit I have (litres, kWh, tonnes)
**so that** the platform normalises it before applying an emission factor.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 06 §6.2 — Unit conversion](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/services.py` · `_apply_unit_conversion()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::test_quantity_canonical_stored_for_audit` (no-unit fallback only) |
| **Linear** | [SUS-20 · CFI-003](https://linear.app/susdevos/issue/SUS-20/cfi-003-define-and-enforce-the-canonical-emission-unitfactor-contract) · `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** `InputUnitId` is set and that `Units` row has a non-null `ConversionFactor`,
   **when** `_apply_unit_conversion()` runs,
   **then** `QuantityCanonical = QuantityOrCost × InputUnitId.ConversionFactor` — **no test in the suite creates a `Units` row with a real conversion multiplier and asserts this product**; every existing test either omits `InputUnitId` entirely or does not assert a multiplier effect.
2. **Given** no `InputUnitId` is supplied,
   **when** the same function runs,
   **then** `QuantityCanonical` falls back to the raw `QuantityOrCost` unchanged (`test_quantity_canonical_stored_for_audit` — asserts only that the field is non-null, not its value).
3. **Given** `_compute_amounts()` reads the canonical quantity with `instance.QuantityCanonical if instance.QuantityCanonical is not None else instance.QuantityOrCost`,
   **when** a legitimately zero `QuantityCanonical` is set,
   **then** it is used as-is (`0`), not silently replaced by the raw quantity — the `is None` check (not truthiness) is deliberate, per the comment at `services.py:46-48`, but **this zero-quantity edge case has no test**.

---

<a id="sdo-ghg-04"></a>

### SDO-GHG-04 · Scope 2 always populates BOTH location-based and market-based amounts

**As a** sustainability contributor
**I want** a Scope 2 electricity record to report both methods
**so that** the inventory conforms to the GHG Protocol Scope 2 Guidance's dual-reporting requirement.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 — Scope 2 dual-method detail](../diagrams/bpmn/02-emissions-lifecycle.md) |
| **Code** | `backend/apps/emissions/services.py` · `_compute_scope2()` |
| **Tests** | `backend/apps/emissions/tests/test_services.py::test_scope2_dual_method_uses_separate_factors`, `test_scope2_market_falls_back_to_location_when_absent`, `test_scope2_fallback_amounts_refresh_on_edit` |
| **Linear** | [SUS-23 · CFI-004](https://linear.app/susdevos/issue/SUS-23/cfi-004-capture-evidenced-scope-2-location-and-market-methods) · `area:ghg` · `risk:data-loss` |

**Acceptance criteria**

1. **Given** a Scope 2 record with both `EFLocationBased="0.5"` and `EFMarketBased="0.1"` and `QuantityCanonical=1000`,
   **when** it is saved,
   **then** `EmissionsAmountLocationBased == 500.0000` and `EmissionsAmountMarketBased == 100.0000` — distinct values from distinct factors (`test_scope2_dual_method_uses_separate_factors`).
2. **Given** only `EFLocationBased` is supplied (no `EFMarketBased`),
   **when** the record is saved,
   **then** `EmissionsAmountMarketBased` falls back to `EmissionsAmountLocationBased`'s value — both columns are always populated, even from a single input (`test_scope2_market_falls_back_to_location_when_absent`).
3. **Given** the primary `EmissionsAmount`/`EmissionsAmountTonnes` fields on a Scope 2 record,
   **when** both location and market amounts are available,
   **then** the primary figure equals the **market-based** amount, not location-based (`_compute_scope2`, `test_scope2_primary_amount_is_market_based`).
4. **Given** a legacy Scope 2 record with no explicit `EFLocationBased`/`EFMarketBased` (both fall back to the generic `EmissionFactor` result),
   **when** it is edited and re-saved with a changed `QuantityOrCost`,
   **then** `EmissionsAmountLocationBased`, `EmissionsAmountMarketBased`, and the primary `EmissionsAmount` all recompute from the new quantity — the fallback branches use `else` (not `elif ... is None`), so a re-save refreshes rather than retaining the first-save value (`test_scope2_fallback_amounts_refresh_on_edit`, regression-tested explicitly).
5. **Given** the first-party emission form, **when** a user records Scope 2 activity,
   **then** it can select only one generic library factor and cannot provide distinct,
   evidenced location- and market-based inputs. The service-level dual calculation is built,
   but the product flow can therefore collapse both columns to the same fallback value. This
   unmet capture criterion is tracked by SUS-23 and is why the story remains 🟡 Partial.

---

### SDO-GHG-05 · Biogenic CO2 is computed separately and excluded from the GWP total

**As a** sustainability contributor
**I want** biogenic CO2 (from biomass/biofuel combustion) reported apart from the fossil total
**so that** the inventory follows GHG Protocol §9's separate-reporting requirement.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 06 §6.2 — Biogenic CO2](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/services.py` · `_compute_amounts()` |
| **Tests** | `backend/apps/emissions/tests/test_services.py::test_biogenic_co2_computed_and_excluded_from_total`, `test_no_biogenic_factor_leaves_field_null` |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** a Scope 1 record with `EmissionFactor=2.0`, `BiogenicCO2FactorKg=0.3`, and `QuantityCanonical=1000`,
   **when** it is saved,
   **then** `EmissionsAmount == 2000.0000` (fossil total, unaffected by the biogenic factor) and `BiogenicCO2AmountTonnes == 0.300000` (`1000 × 0.3 / 1000`) — computed and stored separately, never added into the GWP total (`test_biogenic_co2_computed_and_excluded_from_total`).
2. **Given** no `BiogenicCO2FactorKg` is supplied,
   **when** the record is saved,
   **then** `BiogenicCO2AmountTonnes` is `None` (`test_no_biogenic_factor_leaves_field_null`).
3. **Given** a record previously had `BiogenicCO2FactorKg` set (and a resulting non-null `BiogenicCO2AmountTonnes`),
   **when** it is re-saved with `BiogenicCO2FactorKg` cleared to `None`,
   **then** `BiogenicCO2AmountTonnes` is also cleared to `None` — the `else` branch explicitly nulls the derived figure so a record that stops being biogenic does not keep reporting a stale amount (`services.py:62-65`). **This specific clear-on-re-save transition has no test**; only the "never set" case (criterion 2) is covered.

---

### SDO-GHG-06 · Scope 3 records carry a category 1–15

**As a** sustainability contributor
**I want** to record Scope 3 (value-chain) emissions with a GHG Protocol category
**so that** the inventory can cover indirect emissions.

| | |
|---|---|
| **Status** | ✅ Built — no longer gated |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 — Feature gate](../diagrams/bpmn/02-emissions-lifecycle.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet._require_scope3_feature()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestScope3UnderServiceTierPackaging` |
| **Linear** | `area:ghg` · `type:billing` |

**Acceptance criteria**

1. **Given** an entity with no subscription at all,
   **when** `POST /api/emissions/` is submitted with `Scope=3`,
   **then** it succeeds `201` (`test_create_scope3_allowed_without_any_plan`). Gating a whole
   GHG Protocol scope sat badly with the product premise — a Scope 1/2-only inventory is not a
   corporate footprint — so Scope 3 ships on every plan.
2. **Given** the same entity,
   **when** `POST /api/emissions/` is submitted with `Scope=1` or `Scope=2`,
   **then** it succeeds `201` (`test_create_scope1_allowed_without_any_plan`).
3. **Given** an existing Scope 1/2 record,
   **when** it is `PATCH`ed to `{"Scope": 3}`,
   **then** the update succeeds `200` (`test_patch_record_to_scope3_allowed_without_any_plan`).
4. **Given** `FEATURE_GATES_ENABLED` is switched back on and the entity lacks `scope_3`,
   **when** a Scope 3 record is created,
   **then** it is rejected `402` with `{"code": "feature_gated", "feature": "scope_3", ...}`
   (`test_gate_still_denies_when_enforcement_is_switched_on`). The gate is server-enforced on
   the write path whenever it is on — per [F5](../diagrams/FINDINGS.md#f5) the status is `402`,
   not `403`.

---

### SDO-GHG-07 · Emission factors are chosen from a factor set; Climatiq sync refreshes the library weekly

**As a** sustainability contributor
**I want** to pick an emission factor from a maintained library
**so that** I don't have to source and enter factor values myself.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above (browsing); system (sync) |
| **Diagram** | [UML 03 — Reference data](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionFactorsViewSet`, `EmissionFactorSetsViewSet` · `backend/tasks/integrations/climatiq.py` · `sync_climatiq_emission_factors()` |
| **Tests** | `backend/tasks/tests/test_beat_schedule.py` (registration/scheduling only — asserts the task name resolves, not its logic) |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** `GET /api/emission-factors/`,
   **when** filtered with `?scope=`, `?scope3=`, `?set_id=`, `?gas=`, `?country=`, or `?year=`,
   **then** results are narrowed accordingly, restricted to factors whose `EmissionFactorSets` row is `IsActive=True, Status=1` (`EmissionFactorsViewSet.get_queryset()`) — **none of these filters has a test**.
2. **Given** `sync_climatiq_emission_factors` is scheduled weekly (Sunday 02:00 UTC per its module docstring),
   **when** it runs,
   **then** it refreshes every `EmissionFactors` row with a non-null `ClimatiqActivityId` whose `ExternalSyncedAt` is `NULL` or older than 7 days (`STALE_AFTER`), via `_refresh_factor()`.
3. **Given** `CLIMATIQ_API_KEY` is unset,
   **when** the sync task runs,
   **then** it logs a warning and returns `{"skipped": "CLIMATIQ_API_KEY not configured"}` rather than raising — the beat schedule is never crashed by a missing key.
4. Criteria 2 and 3 have **no dedicated test file** (`backend/tasks/tests/` has no `test_climatiq.py`); `test_beat_schedule.py` only confirms the task name is registered with Celery, not that its refresh/stale-cache/skip logic behaves as described.

---

### SDO-GHG-08 · A GWP dataset determines the gas multiplier; a missing GWP row is logged loudly, not silently treated as 1

**As a** sustainability contributor
**I want** non-CO2 gases correctly weighted by their global warming potential
**so that** CH4 and N2O emissions aren't undercounted as if they were CO2.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 03 — GWP datasets/values](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/services.py` · `_get_gwp_factor()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::test_scope1_ch4_applies_gwp_factor` (happy-path lookup only) |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** a Scope 1 record with `Gas="CH4"`, `GasSubtype="fossil"`, `EmissionFactor="0.00200000"`, `QuantityOrCost=100`, and the seeded IPCC AR6 GWP100 dataset (`CH4/fossil → 29.8`),
   **when** it is saved,
   **then** `EmissionsAmount == 5.9600` (`100 × 0.002 × 29.8`) — the GWP100 multiplier is correctly applied (`test_scope1_ch4_applies_gwp_factor`).
2. **Given** a gas/subtype combination with no matching `GwpValues` row in the record's `GwpDatasetId`,
   **when** `_get_gwp_factor()` is called,
   **then** it retries once without the subtype (recovering a canonical `(Gas, None)` row), and if that also misses, logs a `logger.warning` naming the gas, subtype and dataset, and falls back to `1` — **this fallback-and-log path has no test**; only the successful-lookup case is exercised.
3. **Given** more than one `GwpValues` row matches (`MultipleObjectsReturned`),
   **when** `_get_gwp_factor()` is called,
   **then** it logs a warning and falls back to `1` rather than raising — **also untested**. The `GwpValues` model does carry a `unique_gwp_gas_per_dataset` constraint on `(GwpDatasetId, Gas, GasSubtype)`, so this branch can only be reached via a subtype-retry collision, not a direct duplicate.
4. **Given** `instance.GwpDatasetId is None`,
   **when** `_get_gwp_factor()` is called,
   **then** it returns `1` (CO2-equivalent passthrough) without any warning — a missing *dataset* is treated as a deliberate opt-out, distinct from a missing *row* within a configured dataset, which is logged loudly. **Untested.**

---

### SDO-GHG-09 · Spend-based factors depend on FX rates synced daily from the ECB

**As a** sustainability contributor entering spend-based Scope 3 data
**I want** my local-currency spend converted to USD using a current exchange rate
**so that** spend-based emission factors (denominated in USD) can be applied consistently.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above (recording); system (FX sync) |
| **Diagram** | [UML 03 — Currency](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/tasks/integrations/fx.py` · `sync_ecb_fx_rates()`, `sync_oer_fx_rates()` · `backend/apps/emissions/models.py` · `EmissionsData.SpendAmountUSD`, `.ExchangeRateToUSD` |
| **Tests** | `backend/tasks/tests/test_fx.py::test_oer_rate_is_stored_inverted_to_usd_per_currency` |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** `sync_ecb_fx_rates` runs daily at 17:00 UTC,
   **when** it succeeds,
   **then** it upserts one `ExchangeRates` row per tracked currency (`FromCurrency` → `ToCurrency="USD"`, `RateDate=today`), cross-multiplying each currency's EUR rate against EUR/USD (`ExchangeRates.objects.update_or_create`).
2. **Given** the ECB EUR/USD fetch itself fails,
   **when** `sync_ecb_fx_rates` handles the exception,
   **then** it dispatches `sync_oer_fx_rates.delay()` as a fallback and returns `{"skipped": "ECB EUR/USD unavailable, OER triggered"}` rather than raising.
3. **Given** Open Exchange Rates quotes currency-per-USD from a USD base, while `ExchangeRates.Rate` is consumed as USD-per-`FromCurrency`,
   **when** `sync_oer_fx_rates` upserts a rate,
   **then** it stores the *inverted* value (`1 / oer_rate`) so the two sync sources are consistent (`test_oer_rate_is_stored_inverted_to_usd_per_currency`).
4. **Given** `EmissionsData.SpendAmountUSD` and `.ExchangeRateToUSD` are declared in `CALCULATED_FIELDS` (server-computed, client-writable stripped by the serializer) alongside `EmissionsAmount`,
   **when** the codebase is searched for any code that reads `ExchangeRates` while computing an `EmissionsData` record,
   **then** none was found — `compute_emissions()` / `_compute_amounts()` never touch `ExchangeRates`, `SpendAmountLocal`, `SpendCurrency`, or populate `SpendAmountUSD`/`ExchangeRateToUSD`. The ECB/OER sync populates the `ExchangeRates` table correctly (criteria 1–3, tested), but **nothing in the emissions calculation path consumes it** — a spend-based record's USD conversion fields are reserved and protected as "server-computed" yet nothing computes them. This is the reason for the 🟡 status, and is closer to an unimplemented join than an untested one.

---

<a id="sdo-ghg-10"></a>

### SDO-GHG-10 · An emission can be attached to a project and phase

**As a** sustainability contributor
**I want** to associate an emissions record with a development project and its phase
**so that** project-level GHG reporting is possible.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 — Capture and relationship validation](../diagrams/bpmn/02-emissions-lifecycle.md) · [UML 03 — Inventory and emissions records](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `frontend/src/app/(app)/projects/[id]/page.tsx` · `frontend/src/app/(app)/emissions/page.tsx` · `backend/apps/projects/views.py` · `backend/apps/emissions/serializers.py` |
| **Tests** | `backend/apps/projects/tests/test_project_phases.py` · `backend/apps/emissions/tests/test_relationship_integrity.py` |
| **Linear** | [SUS-25 · CFI-008](https://linear.app/susdevos/issue/SUS-25/cfi-008-connect-project-phases-and-inventory-assignment-end-to-end) · [SUS-22 · CFI-006](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship) |

**Acceptance criteria**

1. **Given** a same-tenant project, **when** a user opens its detail page, **then** they can
   create, edit, list, and remove unused phases through
   `/api/projects/{projectId}/phases/`; a phase already referenced by emissions returns
   `409 phase_in_use` instead of silently detaching operational data.
2. **Given** the emission create or detail flow, **when** a project is selected, **then** the
   phase selector lists that project's phases and the selected `ProjectId`/`PhaseId`
   round-trip through the API and database.
3. **Given** a phase and project that do not match, or any project/phase owned by another
   entity, **when** the emission is created or edited, **then** validation returns HTTP 400
   and writes nothing (`test_phase_must_belong_to_selected_project`,
   `test_foreign_project_phase_and_inventory_are_rejected`).
4. **Given** `GET /api/emissions/?projectId=<id>` or `?phaseId=<id>`, **when** called,
   **then** `get_queryset()` applies the selected relationship filter. These filter paths
   remain candidates for dedicated response-level tests under SDO-GHG-12.

---

### SDO-GHG-11 · Per-gas line-item detail rows

**As a** sustainability contributor
**I want** to break an emissions record down into sub-meter or per-gas line items
**so that** the record's total can be traced to its component activity data.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above (add); locked once the parent record is verified |
| **Diagram** | [UML 03 — EmissionsDetails](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `backend/apps/emissions/models.py` · `EmissionsDetails` · `backend/apps/emissions/views.py` · `EmissionsDataViewSet.details()`, `.detail_item()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestVerificationImmutability::test_line_items_of_verified_record_are_immutable` (lock behaviour only) |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** `POST /api/emissions/{id}/details/` with `Description`, `QuantityOrCost`, `Unit`, `EmissionFactor`, `Gas`, `GasSubtype`, `GwpDatasetId`,
   **when** the record is still editable (`VerificationStatus < 3` and no verified parent inventory),
   **then** the detail row is created `201` and linked to the parent via `EmissionsId` (`test_line_items_of_verified_record_are_immutable`, which creates a detail as its setup step).
2. **Given** `EmissionsDetailsSerializer` marks `EmissionsAmount` and `EmissionsAmountTonnes` as `read_only_fields` (declared server-computed, matching the naming convention `EmissionsData` uses for its own calculated fields),
   **when** the `EmissionsDetails` model is inspected,
   **then** it has **no `save()` override** — unlike `EmissionsData.save()`, which calls `compute_emissions()`. Nothing in the codebase computes a detail row's own `EmissionsAmount`/`EmissionsAmountTonnes` from its `QuantityOrCost × EmissionFactor × GWP`; they are write-protected from the client but never populated by the server either, so they persist as `NULL` indefinitely. Only the parent `EmissionsData` row's total is authoritative — the per-line amount this story's name implies ("per-gas line-item detail") does not actually exist as a computed figure.
3. **Given** a verified parent record or one whose parent `GHGInventories` is verified,
   **when** `POST .../details/`, `PATCH .../details/{id}/`, or `DELETE .../details/{id}/` is attempted,
   **then** all three are rejected `403` with `{"code": "verified_immutable"}` (`test_line_items_of_verified_record_are_immutable`, `TestVerifiedInventoryLineItemLock`).

---

### SDO-GHG-12 · Listing and filtering emissions by scope

**As a** sustainability manager
**I want** to filter the emissions list by scope, project, phase, verification status, or reporting year
**so that** I can review a specific slice of the entity's inventory.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 — Main process](../diagrams/bpmn/02-emissions-lifecycle.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet.get_queryset()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py::TestEmissionsFilters` (`?scope=`, `?verificationStatus=` only) |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** three records at Scope 1, 2, and 3 respectively,
   **when** `GET /api/emissions/?scope=1` is called,
   **then** only the Scope 1 record is returned (`test_filter_by_scope`).
2. **Given** a verified record among unverified ones,
   **when** `GET /api/emissions/?verificationStatus=3` is called,
   **then** the verified record is included in the results (`test_filter_by_verification_status`).
3. **Given** `get_queryset()` also supports `?projectId=`, `?phaseId=`, and `?reportingYear=` (`views.py:71-80`),
   **when** the test suite is searched,
   **then** none of these three list filters has a dedicated response test — only `?scope=`
   and `?verificationStatus=` are verified. Project/phase relationship writes and consistency
   are covered separately by SDO-GHG-10.
4. **Given** the list response,
   **when** its shape is inspected,
   **then** it uses `EmissionsDataListSerializer` with the bounded review fields
   `EmissionsId`, `Title`, `Scope`, `Scope3Category`, `Gas`, `EmissionsAmountTonnes`,
   `VerificationStatus`, `ProjectId`, `PhaseId`, `InventoryId`, reporting-period dates,
   `ReportingYear`, and `Status`, rather than the full detail/create serializer.

---

### SDO-GHG-13 · Emissions belonging to a verified inventory cannot be edited

**As a** compliance officer
**I want** every row inside a verified GHG inventory to be frozen, not just individually-verified records
**so that** the inventory's audit-locked totals can never silently diverge from the data they represent.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above (blocked); SuperAdmin (unlock) |
| **Diagram** | [BPMN 03](../diagrams/bpmn/03-inventory-verification.md) · [UML 06 §6.3 — Verification and unlock](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/views.py` · `EmissionsDataViewSet._inventory_locked_response()`, `._verified_lock_response()` · `backend/apps/emissions/models.py` · `GHGInventories.VerificationStatus` |
| **Tests** | `backend/apps/emissions/tests/test_verified_immutability.py` (full suite) |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** an `EmissionsData` row whose parent `GHGInventories.VerificationStatus >= 3`, even though the row itself was **never individually verified** (verifying an inventory does not cascade `VerificationStatus` to its member rows),
   **when** `PATCH` or `DELETE` is attempted on that row,
   **then** both are rejected `403` with `{"code": "verified_immutable"}` (`TestVerifiedInventoryChildRows::test_edit_row_in_verified_inventory_returns_403`, `test_delete_row_in_verified_inventory_returns_403`).
2. **Given** a verified inventory,
   **when** `POST /api/emissions/` is submitted with that `InventoryId`,
   **then** it is rejected `403` — new rows cannot be added to a frozen inventory (`test_add_row_to_verified_inventory_returns_403`).
3. **Given** an editable, standalone record (no `InventoryId`),
   **when** it is `PATCH`ed to set `InventoryId` to a verified inventory,
   **then** the re-point is rejected `403` — `update()` validates the *target* inventory even though the row's *current* `InventoryId` was still editable, closing a bypass the `create()` guard alone would miss (`test_reassign_row_into_verified_inventory_returns_403`).
4. **Given** a record's own detail/offset line items, or an offset reached via the standalone `EmissionsOffsetsViewSet` (`/api/emissions-offsets/`),
   **when** the parent record is locked either by its own `VerificationStatus >= 3` or by its parent inventory's `VerificationStatus >= 3`,
   **then** every write path — nested details, nested offsets, and the standalone offsets endpoint — is rejected `403` with `{"code": "verified_immutable"}` (`TestVerifiedInventoryLineItemLock`, `TestStandaloneOffsetVerifiedLock`) — this closes what the test file's module docstring calls out as three found gaps (F1–F3 in that file's own numbering, distinct from the FINDINGS.md register).

---

<a id="sdo-ghg-14"></a>

### SDO-GHG-14 · Source context and reporting period survive emission capture

**As a** sustainability contributor
**I want** the period, supplier, activity context, and operational relationships I enter to
be preserved
**so that** a reviewer can trace a calculated figure back to the source evidence and boundary.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [BPMN 02 §Capture and lineage integrity](../diagrams/bpmn/02-emissions-lifecycle.md) · [UML 03 §Field lineage](../diagrams/uml/03-domain-ghg.md) |
| **Code** | `frontend/src/app/(app)/emissions/page.tsx` · `backend/apps/emissions/models.py` · `backend/apps/emissions/serializers.py` |
| **Tests** | `backend/apps/emissions/tests/test_relationship_integrity.py` · `backend/apps/emissions/tests/test_api.py` |
| **Linear** | [SUS-21 · CFI-001](https://linear.app/susdevos/issue/SUS-21/cfi-001-stop-silently-discarding-emission-form-fields) · [SUS-22 · CFI-006](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship) · [SUS-25 · CFI-008](https://linear.app/susdevos/issue/SUS-25/cfi-008-connect-project-phases-and-inventory-assignment-end-to-end) |

**Acceptance criteria**

1. **Given** the first-party form, **when** a user submits `ReportingPeriodFrom`,
   `ReportingPeriodTo`, `SupplierName`, `ActivityDescription`, and optional
   `ProjectId`/`PhaseId`/`InventoryId`, **then** those exact keys persist and round-trip in
   the detail/edit view; the legacy mismatched keys `DateFrom`, `DateTo`, `Supplier`, and
   `Remarks` are no longer emitted.
2. **Given** one reporting-period date without the other, an end before the start, or a
   `ReportingYear` different from the period end year, **when** validation runs, **then** it
   returns field-specific HTTP 400 errors rather than saving an ambiguous period.
3. **Given** an inventory assignment, **when** the record period falls outside the inventory
   period, the year differs, or an explicitly supplied GWP dataset differs, **then** the API
   rejects the assignment. A valid assignment adopts the inventory's recorded GWP dataset.
4. **Given** an unrecognised request key, **when** the emission serializer receives it,
   **then** the API returns HTTP 400 naming the unknown field; visible user input is never
   silently ignored.

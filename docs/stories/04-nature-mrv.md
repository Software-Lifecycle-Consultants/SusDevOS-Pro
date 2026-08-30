# 04 — Nature & MRV

Land, ecosystems, species, and the two carbon-flux processes — tree removals (a one-off
stock loss) and restorations (time-growing sequestration) — plus carbon-credit MRV against
the Verra and Gold Standard registries. IDs `SDO-NAT-*`.

Most of the IPCC LULUCF *formula* work here is solidly tested at the service layer
(`apps/restorations/tests/test_services.py`); most of the *API* layer around it — posting a
removal, a restoration, an affected species, a species search — has thin or no test
coverage, so several stories below are 🟡 Partial for that reason specifically, not because
the behaviour is wrong. One story (threatened-species flagging) is a genuine ⬜ Gap: nothing
in the codebase inspects `IUCNStatus` at all.

---

### SDO-NAT-01 · Register a land parcel with a geographic boundary

**As a** project manager
**I want** to register a land parcel with its boundary
**so that** ecosystems, tree removals and restorations can be linked to a real location.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Land & ecosystem](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/land/models.py` · `backend/apps/land/geo.py` · `backend/apps/land/integrations.py` · `backend/apps/land/serializers.py` · `backend/apps/land/views.py` · `frontend/src/components/land/MapPicker.tsx` |
| **Tests** | `backend/apps/land/tests/test_boundary_area.py` · `backend/apps/land/tests/test_geocode.py` · `backend/apps/land/tests/test_feature_gate.py` |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

*Defining the parcel*

1. **Given** any authenticated tenant — no plan feature required — **when**
   `POST /api/land-parcels/` is called with `ParcelName` (and optionally `BoundaryGeoJSON`,
   `AreaHectares`), **then** the response is `201` with `EntityId` set from
   `request.entity_id` (`test_create_land_parcel_allowed_without_any_plan`).
2. **Given** the user draws a boundary on the map, **when** they click corner by corner,
   **then** each click adds a vertex, any vertex can be dragged to adjust it, and the
   enclosed area updates live in hectares beside the map.
3. **Given** a polygon boundary is submitted with no `AreaHectares`, **when** it is saved,
   **then** the server derives `AreaHectares` from the geometry so the figure always matches
   the shape (`test_polygon_without_an_area_derives_one`). A `null` area counts as absent,
   because the create form always sends the key
   (`test_null_area_alongside_a_polygon_still_derives`).
4. **Given** a non-empty `AreaHectares` is submitted alongside the boundary, **when** it is
   saved, **then** the supplied value wins — a legal title area may legitimately differ from
   the mapped shape (`test_explicit_area_overrides_the_polygon`).
5. **Given** the boundary is a `Point` pin or a line, **when** it is saved, **then**
   `AreaHectares` is left untouched rather than zeroed — those shapes enclose no area
   (`test_point_pin_leaves_area_empty`).
6. **Given** an existing parcel is re-drawn, **when** only `BoundaryGeoJSON` is `PATCH`ed,
   **then** the area is recomputed (`test_redrawing_the_boundary_updates_the_area`); editing
   an unrelated field leaves it alone (`test_editing_an_unrelated_field_leaves_the_area_alone`).
7. **Given** `BoundaryGeoJSON` is not a GeoJSON object, **when** it is submitted, **then**
   the response is `400` naming the field rather than storing unrenderable JSON
   (`test_non_geojson_boundary_is_rejected`).

*Finding the site*

8. **Given** the user types at least three characters into the map search box, **when** the
   debounce elapses, **then** `GET /api/land-parcels/geocode/?q=` returns candidate places
   and selecting one fits the map to its bounding box, or centres on it when the provider
   gives no box (`test_returns_matches`).
9. **Given** the geocoding provider is down or slow, **when** a search runs, **then** the
   response is `200` with an empty list rather than a `500` — a search box that finds nothing
   beats a broken page (`test_provider_outage_is_an_empty_list_not_a_500`).
10. **Given** the lookup proxies Nominatim, **when** it calls out, **then** it sends an
    identifying `User-Agent` and caches results, so the tenant's browser never contacts the
    provider directly and the 1 req/sec policy is respected
    (`test_sends_an_identifying_user_agent`, `test_repeat_query_is_served_from_cache`). The
    endpoint is throttled at `30/min` per user.
11. **Given** the user clicks *My location*, **when** the browser grants permission, **then**
    the map centres on their position; a denial shows a message pointing at the search box
    instead of failing silently.

*Known limits*

12. **Given** `BoundaryGeoJSON` is a plain `JSONField` storing GeoJSON — not a PostGIS
    `GeometryField`, despite CLAUDE.md describing the stack as "PostgreSQL/PostGIS 3.4" —
    **then** there is no spatial indexing or spatial query support on this field. Area is
    computed in Python (`apps/land/geo.py`) using the same spherical-excess formula the
    browser uses, so the live readout and the stored value agree; validation is structural
    (is it GeoJSON?) rather than geometric (is the ring simple and non-self-intersecting?).
13. **Given** gating is switched back on (`FEATURE_GATES_ENABLED=True`) and the plan lacks
    `land_parcel_gis`, **when** the API is called, **then** the response is `402`
    (`test_gate_still_denies_when_enforcement_is_switched_on`).

---

### SDO-NAT-02 · Record the ecosystems present on a parcel

**As a** project manager
**I want** to link ecosystems to a land parcel
**so that** the parcel's habitat composition is recorded against the entity's own data only.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Land & ecosystem](../diagrams/uml/04-domain-nature-mrv.md) |
| **Code** | `backend/apps/land/views.py` · `LandParcelsViewSet.ecosystems()`/`.unlink_ecosystem()` · `backend/apps/land/models.py` · `LandParcelEcosystems` |
| **Tests** | `backend/apps/land/tests/test_ecosystem_link_isolation.py` |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a parcel and an `Ecosystem` belonging to the *same* entity, **when**
   `POST /api/land-parcels/{id}/ecosystems/` is called with `{"EcosystemId": ...}`,
   **then** the response is `201` and a `LandParcelEcosystems` row is created
   (`test_can_link_own_ecosystem`).
2. **Given** an `EcosystemId` belonging to a *different* tenant, **when** the same `POST` is
   made, **then** the response is `404` and no link row is created — the lookup filters
   `Ecosystem.objects.filter(EcosystemId=eco_id, EntityId=parcel_entity_id, ...)`
   (`test_cannot_link_other_tenant_ecosystem`).
3. **Given** a cross-tenant link somehow exists in the join table already, **when**
   `GET /api/land-parcels/{id}/ecosystems/` is called, **then** the other tenant's ecosystem
   is excluded from the response (`test_get_excludes_cross_tenant_ecosystem`).

---

### SDO-NAT-03 · Add a species, enriched from GBIF taxonomy and IUCN Red List status

**As a** project manager
**I want** a species record I create to be auto-enriched with canonical taxonomy and
conservation status
**so that** I don't have to look them up manually, and the record never fails to save
because an external service is down.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above (`ecosystem_basic` feature required) |
| **Diagram** | [UML 04 §External species enrichment](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §L2](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/ecosystem/integrations.py` · `search_species()`, `get_iucn_status()`, `enrich_species()` · `backend/apps/ecosystem/views.py` · `SpeciesViewSet.perform_create()`/`.search()` |
| **Tests** | none |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a client `POST`s `/api/species/` with `CommonName` only, **when**
   `perform_create()` runs, **then** `enrich_species()` best-effort fills
   `ScientificName`/`GBIFKey`/`Family`/`Kingdom` from GBIF's `/v1/species/suggest`
   (`taxonomicStatus == "ACCEPTED"` only) without blocking the create response, wrapped in
   `try/except Exception` at the call site.
2. **Given** `ScientificName` is resolved and `IUCNStatus` is blank, **when** enrichment
   runs, **then** `get_iucn_status()` queries the IUCN Red List API (requires
   `IUCN_API_KEY`) and sets `IUCNStatus`/`IUCNSyncedAt` only if the returned category is one
   of the 9 valid codes (`LC, NT, VU, EN, CR, EW, EX, DD, NE`).
3. **Given** GBIF or IUCN is unreachable, times out, or returns malformed JSON, **when**
   enrichment runs, **then** it logs a warning and returns `[]`/`None` rather than raising —
   species creation never fails because an external service is down.

*Note: `apps/ecosystem/integrations.py` has zero test coverage — no test mocks GBIF/IUCN or
asserts enrichment behaviour on create.*

---

### SDO-NAT-04 · Record a tree removal, listing the species removed with counts and volume

**As a** project manager
**I want** to record which species were removed, with tree counts and merchantable volume
**so that** the biomass carbon lost can be computed.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Tree removals](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §Tree removal](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/models.py` · `TreeRemovals`, `TreeRemovalRemovedSpecies` · `backend/apps/restorations/views.py` · `TreeRemovalsViewSet.removed_species()` |
| **Tests** | `backend/apps/restorations/tests/test_services.py` (service layer only — no API-level test) |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a `TreeRemovals` row, **when**
   `POST /api/tree-removals/{id}/removed-species/` is called with `SpeciesId`, `Count` and
   `VolumeM3` (merchantable timber volume in m³ — a **per-removal total**, not a per-tree
   DBH/height measurement), **then** the response is `201` and the row is linked via
   `TreeRemovalId`.
2. **Given** `BiomassCalculationMethod` is one of the four IPCC tier choices, **when** it is
   *not* `4` (Manual), **then** the volume-based Tier-1 formula runs regardless of whether
   `1`, `2` or `3` was selected — Tier 3 ("measured / allometric equations") has no distinct
   implementation in `compute_removed_species_carbon()`; only Tier 4 branches differently.
3. **Given** `BiomassCalculationMethod == 4`, **when** the row saves, **then**
   `TotalCarbonStockLossTonnesCO2e` is the sum of the client-supplied CO2e plus optional
   dead-organic-matter/soil-carbon fields, with no recomputation from `VolumeM3`.

*Note: the formula is unit-tested (`test_removed_species_carbon_tier1_volume`), but no test
exercises `POST /api/tree-removals/{id}/removed-species/` at the API layer.*

---

### SDO-NAT-05 · Removed-species biomass carbon is computed by the IPCC LULUCF method

**As a** sustainability lead
**I want** removed-tree carbon computed by the standard IPCC method
**so that** the figure is defensible against the GHG Protocol / IPCC LULUCF guidance.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | System (computed server-side on every save) |
| **Diagram** | [UML 04 §Biomass carbon calculation](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §L3](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/services.py` · `compute_removed_species_carbon()`, `_param()`, `CO2_C_RATIO` |
| **Tests** | `backend/apps/restorations/tests/test_services.py` (`test_removed_species_carbon_tier1_volume`, `test_tree_removal_total_aggregates_on_save`) |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** `VolumeM3` and `BasicWoodDensity` (D) / `BiomassExpansionFactor` (BEF) /
   `RootToShootRatio` (R) / `CarbonFraction` (CF) resolved via `_param()` — the species'
   own value, else the IPCC default for its `IPCCForestType` — **when** the row saves,
   **then** `AboveGroundBiomassTonnes = V×D×BEF`, `BelowGroundBiomassTonnes = AGB×R`,
   `CarbonStockTonnesC = (AGB+BGB)×CF`, and `CO2EquivalentTonnes = CarbonStock×44/12`
   (test: `10×0.6×1.74=10.44` → `AGB`, chained through to `24.6485` t CO2e).
2. **Given** density, BEF or root-to-shoot cannot be resolved (no species value and no IPCC
   default for the forest type), **when** the row saves, **then** the biomass/carbon
   outputs are left `NULL` rather than silently defaulting to zero
   (`test_removed_species_no_volume_leaves_outputs_null`).
3. **Given** multiple `TreeRemovalRemovedSpecies` rows under one `TreeRemovals`, **when**
   any one saves or deletes, **then** `recompute_tree_removal_total()` sums
   `TotalCarbonStockLossTonnesCO2e` across all of them into `TreeRemovals.TotalBiomassCarbon`
   (`test_tree_removal_total_aggregates_on_save`: `2 × 24.6485 = 49.2970`).

---

### SDO-NAT-06 · Record species affected but not removed — ecological impact with no carbon figure

**As a** project manager
**I want** to record species impacted by a removal but not felled
**so that** the TNFD-relevant ecological impact is captured without implying a carbon loss
that didn't happen.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Tree removals](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §L4](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/models.py` · `TreeRemovalAffectedSpecies` (SpeciesId, Notes — no carbon fields) · `backend/apps/restorations/views.py` · `TreeRemovalsViewSet.affected_species()` |
| **Tests** | none |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a `TreeRemovals` row, **when**
   `POST /api/tree-removals/{id}/affected-species/` is called with `SpeciesId` and `Notes`,
   **then** the response is `201` and the row is linked via `TreeRemovalId` —
   `TreeRemovalAffectedSpecies` carries no biomass/carbon field at all, structurally
   distinct from `TreeRemovalRemovedSpecies`.
2. **Given** an affected-species row, **when** it is saved, **then** no `save()` override
   or service function computes anything from it, and no downstream aggregation into
   `TreeRemovals.TotalBiomassCarbon` occurs.

*Note: no test covers `affected_species`/`affected_species_item` at all.*

---

### SDO-NAT-07 · Threatened species (IUCN CR/EN/VU) are flagged for biodiversity reporting

**As a** sustainability lead
**I want** species with a threatened IUCN status flagged wherever they appear
**so that** biodiversity-sensitive removals stand out in TNFD reporting.

| | |
|---|---|
| **Status** | ⬜ Gap |
| **Role** | — (no such behaviour exists to assign a role to) |
| **Diagram** | [BPMN 06 §L4](../diagrams/bpmn/06-nature-tracking.md) — describes the intended flag |
| **Code** | none — `Species.IUCNStatus` stores the code but nothing reads it to flag CR/EN/VU |
| **Tests** | none |
| **Linear** | [SUS-11](https://linear.app/susdevos/issue/SUS-11) · `area:nat` · `type:feature` |

**Acceptance criteria (target behaviour — nothing below exists today)**

1. A search for "threatened" and for the codes `CR`/`EN`/`VU` used as a set (rather than
   just enum members) across `backend/` returns zero application-code matches — no property,
   serializer field, filter, or report annotation inspects `IUCNStatus` for threatened
   status.
2. Neither `TreeRemovalAffectedSpecies` nor `TreeRemovalRemovedSpecies` carries a computed
   or stored "threatened" flag; the BPMN 06 "⚠️ Flagged for biodiversity reporting" step
   describes intended behaviour, not implemented behaviour.
3. **To close this gap:** add a `Species.is_threatened` property
   (`IUCNStatus in {"CR", "EN", "VU"}`) and surface it on the removed/affected-species
   serializers, so a removal or impact record involving a threatened species is
   distinguishable via the API without a schema change.

---

### SDO-NAT-08 · Record a restoration planting with species, counts and survival rate

**As a** project manager
**I want** to record species planted in a restoration, with counts and expected survival
**so that** sequestration can be computed from realistic surviving-tree numbers.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Restorations](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §Restoration](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/models.py` · `Restorations`, `RestorationSpecies.SurvivalEstimate` (default `0.85`) · `backend/apps/restorations/views.py` · `RestorationsViewSet.species()` |
| **Tests** | `backend/apps/restorations/tests/test_services.py` (service layer only) |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a `Restorations` row, **when**
   `POST /api/restorations/{id}/species/` is called with `SpeciesId`, `Count`,
   `AreaHectares` and optionally `SurvivalEstimate`, **then** the response is `201` and the
   row is linked via `RestorationId`.
2. **Given** `SurvivalEstimate` is omitted, **when** the row saves, **then** it defaults to
   `0.85` (documented as "tropical, unmonitored") rather than treating survival as 100%.
3. **Given** `AnnualSequestrationRateTonnesCO2ePerHa` is omitted on the row, **when** the
   row saves, **then** it falls back to `SpeciesId.AnnualSequestrationRateTonnesCO2ePerHa`.

*Note: the sequestration formula is unit-tested
(`test_restoration_sequestration_formula`), but no test exercises
`POST /api/restorations/{id}/species/` at the API layer.*

---

### SDO-NAT-09 · Restoration sequestration grows with elapsed time since planting

**As a** sustainability lead
**I want** a restoration's reported sequestration to increase year over year
**so that** it reflects real forest growth rather than a fixed one-time estimate.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | System (recomputed on every save of the species row) |
| **Diagram** | [UML 04 §Biomass carbon calculation](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §Important asymmetry](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/services.py` · `compute_restoration_species_sequestration()`, `_years_established()` |
| **Tests** | `backend/apps/restorations/tests/test_services.py` (`test_restoration_sequestration_formula`) |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a `Restorations.StartDate` in the past, **when** `_years_established()` runs
   (on every save of a `RestorationSpecies` row, not only at creation), **then** it returns
   `(today − StartDate).days / 365.25`, quantized to 2 dp — so re-saving the same row later
   yields a larger `YearsEstablished` and a larger `CumulativeSequestrationTonnesCO2e`
   (test asserts `YearsEstablished > 0` and
   `CumulativeSequestrationTonnesCO2e == rate × area × years × survival`).
2. **Given** `StartDate` is in the future, **when** `_years_established()` runs, **then**
   it returns `0` rather than a negative value.
3. **Contrast:** `compute_removed_species_carbon()` (SDO-NAT-05) takes no date input at
   all — `TotalCarbonStockLossTonnesCO2e` is fixed the moment `VolumeM3`/species parameters
   are saved and never grows or shrinks on a later read, unlike restoration sequestration.
   A reviewer must not treat the two figures as symmetric quantities.

---

### SDO-NAT-10 · Record permanence risk on a restoration

**As a** sustainability lead
**I want** to disclose a restoration's reversal risk
**so that** reporting can flag it, even though the platform does not auto-discount for it.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | Staff and above |
| **Diagram** | [UML 04 §Restorations](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §M4](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/restorations/models.py` · `RestorationSpecies.PermanenceRisk` (choices: 1 Low / 2 Medium / 3 High) |
| **Tests** | none |
| **Linear** | `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** a `RestorationSpecies` row, **when** `PermanenceRisk` is set to `1`, `2` or
   `3`, **then** it is stored as-is with no automatic discount applied to
   `CumulativeSequestrationTonnesCO2e` — the model's own `help_text` states "disclosed, not
   auto-deducted."
2. **Given** `LeakageDiscountPercent` is a separate field that *does* discount the
   sequestration figure (`net = gross × (1 − leakage/100)`, SDO-NAT-08's formula),
   **then** `PermanenceRisk` and `LeakageDiscountPercent` are two distinct,
   independently-set risk concepts on the same row.

*Note: no test asserts `PermanenceRisk` is stored or retrievable via the API — only
`LeakageDiscountPercent` is covered (`test_restoration_leakage_discount_applied`).*

---

<a id="sdo-nat-11"></a>

### SDO-NAT-11 · Record a carbon credit offset against an emissions record, with a serial number and registry

**As a** Manager or ESG consultant
**I want** to attach a purchased or retired carbon credit to an emissions record
**so that** it can later be independently validated against its registry.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above (neither route is gated; the standalone route declares an inert `carbon_offsets` gate) |
| **Diagram** | [UML 03 §Inventory and emissions records](../diagrams/uml/03-domain-ghg.md) · [BPMN 04 §Offset capture](../diagrams/bpmn/04-carbon-credit-mrv.md) |
| **Code** | `frontend/src/app/(app)/offsets/page.tsx` · `backend/apps/emissions/serializers.py` · `StandaloneEmissionsOffsetsSerializer` · `backend/apps/emissions/views.py` |
| **Tests** | `backend/apps/emissions/tests/test_offset_validation.py` · `backend/apps/emissions/tests/test_relationship_integrity.py` (`TestStandaloneOffsetIntegrity`) |
| **Linear** | [SUS-31 · CFI-013](https://linear.app/susdevos/issue/SUS-31/cfi-013-make-standalone-offset-creation-preserve-its-parent-emission) · [SUS-22 · CFI-006](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship) |

**Acceptance criteria**

1. **Given** an emissions record, **when**
   `POST /api/emissions/{id}/offsets/` is called with `Title`, `OffsetType`, `Provider`,
   `OffsetAmountTonnes` and optionally `CreditSerialNumber`+`CreditRegistry`, **then** the
   response is `201` with `RegistryValidationStatus == "unverified"` by default
   (`test_add_offset_to_record`).
2. **Given** the nested offsets endpoint requires no billing feature — unlike the
   standalone `/api/emissions-offsets/`, which declares `carbon_offsets` but is inert while gating is off — **when** any
   authenticated tenant member with access to the parent record posts an offset, **then**
   it succeeds regardless of plan.
3. **Given** a `POST` targeting another entity's emissions record, **then** the response is
   `404`, not `403` — the record lookup itself is tenant-scoped
   (`test_offset_for_other_entity_record_returns_404`).
4. **Given** the standalone offsets page, **when** a user creates a credit, **then**
   `EmissionsId` is required and persisted as the same-tenant parent; a missing parent gives
   field-specific HTTP 400, a foreign parent is rejected, and a verified parent returns
   `403 verified_immutable` without writing an offset.
5. **Given** an existing offset, **when** a client tries to move it to another emissions
   record, **then** validation rejects the reparenting. Inventory membership and lock status
   always flow from the immutable parent relationship.

---

<a id="sdo-nat-12"></a>

### SDO-NAT-12 · Offsets are validated nightly against the Verra or Gold Standard registry; only a registry match sets valid

**As a** sustainability lead
**I want** an offset's validity determined by an external registry, not by the person who
entered it
**so that** the offset column is defensible in an assurance context.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | System (Celery: Verra 03:00, Gold Standard 03:30 daily) |
| **Diagram** | [UML 07 §7.4](../diagrams/uml/07-state-machines.md) · [BPMN 04 §Offset capture and validation](../diagrams/bpmn/04-carbon-credit-mrv.md) |
| **Code** | `backend/tasks/integrations/verra.py` · `sync_verra_registry()` · `backend/tasks/integrations/gold_standard.py` · `sync_gold_standard_registry()`, `_validate_one()` |
| **Tests** | `backend/tasks/tests/test_verra.py` (Verra only) · `backend/apps/emissions/tests/test_relationship_integrity.py` (client-forgery/reset guards) |
| **Linear** | [SUS-32 · CFI-014](https://linear.app/susdevos/issue/SUS-32/cfi-014-prevent-clients-from-self-validating-carbon-offsets) · `area:nat` · `risk:security` |

**Acceptance criteria**

1. **Given** an offset with `CreditRegistry == "verra"` (or unset — legacy rows) and
   `RegistryValidationStatus` in `{"pending", "unverified"}`, **when**
   `sync_verra_registry()` streams the Verra CSV and finds the serial, **then**
   `RegistryValidationStatus == "valid"`, `RegistryValidatedAt` is set, and
   `RegistryRetirementBeneficiary` is backfilled from the CSV
   (`test_valid_serial_still_validates`).
2. **Given** the serial is not present in a successfully-downloaded, non-empty CSV,
   **when** the sync completes, **then** `RegistryValidationStatus == "invalid"` — subject
   to the failure-mode carve-outs in SDO-NAT-13.
3. **Given** a Gold Standard offset, **when** `sync_gold_standard_registry()` queries the
   per-project registry and gets a `200` with a project payload, **then**
   `RegistryValidationStatus == "valid"` and `RegistryProjectName`/`Type`/`VintageYear` are
   backfilled from the response; a `404` sets `"invalid"`.
4. **Given** any authenticated API client, **when** it supplies or patches
   `RegistryValidationStatus`, `RegistryValidatedAt`, registry project metadata, vintage, or
   retirement beneficiary, **then** serializer validation returns HTTP 400 naming the
   server-managed fields; a client cannot make an offset deductible.
5. **Given** a user changes credit identity evidence (`CreditSerialNumber`, registry,
   certificate, amount, or validity dates), **when** the edit saves, **then** all prior
   registry result fields are cleared and status resets to `unverified` pending fresh
   external validation.

*Note: client forgery and reset semantics are tested, as is the positive Verra path.
Gold Standard and claim-depth validation remain incomplete under SUS-32, so this story stays
🟡 Partial.*

---

<a id="sdo-nat-13"></a>

### SDO-NAT-13 · A registry that is unreachable must not downgrade offsets to invalid

**As a** sustainability lead
**I want** a registry outage to leave offsets exactly where they were
**so that** a network failure can never be mistaken for a fraudulent credit.

| | |
|---|---|
| **Status** | 🟡 Partial |
| **Role** | System |
| **Diagram** | [BPMN 04 §Failure semantics](../diagrams/bpmn/04-carbon-credit-mrv.md) |
| **Code** | `backend/tasks/integrations/verra.py` (retries on `RequestException`; aborts on an empty/truncated CSV) · `backend/tasks/integrations/gold_standard.py::_validate_one()` (returns `"pending"` on `RequestException`) |
| **Tests** | `backend/tasks/tests/test_verra.py` (`test_empty_csv_does_not_invalidate_pending_offsets`) |
| **Linear** | [SUS-32 · CFI-014](https://linear.app/susdevos/issue/SUS-32/cfi-014-prevent-clients-from-self-validating-carbon-offsets) · `area:nat` · `type:spec` |

**Acceptance criteria**

1. **Given** the Verra CSV download raises `requests.RequestException`, **when**
   `sync_verra_registry()` runs, **then** it calls `self.retry(exc=exc)` before touching
   any `EmissionsOffsets` row — no offset's `RegistryValidationStatus` changes.
2. **Given** the Verra CSV downloads successfully but parses to zero serial numbers
   (truncated/empty), **when** the sync runs, **then** it aborts and returns
   `{"skipped": "empty or unparseable CSV", ...}` without invalidating any pending offset
   (`test_empty_csv_does_not_invalidate_pending_offsets`) — because the requery only
   reconsiders `pending`/`unverified` rows, an incorrect mass-invalidation here would be
   permanent.
3. **Given** a Gold Standard lookup raises `RequestException`, **when** `_validate_one()`
   runs, **then** it returns `"pending"` (not `"invalid"`), and the caller's loop increments
   `deferred` and issues no `.save()` for that offset — its prior status is untouched.

*Note: the tested scenario is the empty-CSV case, not a literal `RequestException` for
Verra, and the Gold Standard path (item 3) has no test at all — confirmed by reading
`_validate_one()`, not by a passing test.*

---

<a id="sdo-nat-14"></a>

### SDO-NAT-14 · Offsets are reported separately from gross emissions and never netted into EmissionsAmount

**As a** sustainability lead
**I want** gross emissions to stay gross
**so that** offsetting can never quietly deflate the headline emissions figure.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | System |
| **Diagram** | [BPMN 04 §Where offsets sit relative to gross emissions](../diagrams/bpmn/04-carbon-credit-mrv.md) |
| **Code** | `backend/apps/emissions/services.py` · `compute_emissions()` (no offset lookup) · `backend/tasks/emissions.py` · `_compute_inventory_totals()` (`NetEmissionsTonnes` as a distinct field) |
| **Tests** | `backend/apps/emissions/tests/test_offset_validation.py` (`TestOffsetNetTotalRule`) |
| **Linear** | [SUS-31 · CFI-013](https://linear.app/susdevos/issue/SUS-31/cfi-013-make-standalone-offset-creation-preserve-its-parent-emission) · [SUS-33 · CFI-015](https://linear.app/susdevos/issue/SUS-33/cfi-015-compute-formal-inventory-totals-from-explicit-inventory) |

**Acceptance criteria**

1. **Given** an `EmissionsData` row with offsets attached, **when** `compute_emissions()`
   runs on any save, **then** `EmissionsAmount`/`EmissionsAmountTonnes` are computed purely
   from `QuantityCanonical × EmissionFactor × GWP` — there is no offset lookup anywhere in
   `apps/emissions/services.py`.
2. **Given** only server-validated `RegistryValidationStatus == "valid"` offsets reduce
   `GHGInventories.NetEmissionsTonnes` (a separate, inventory-level field recomputed on
   submit/verify and by the nightly refresh), **when** a record has
   `unverified`/`pending`/`invalid` offsets attached,
   **then** its own `EmissionsAmountTonnes` is unaffected, and those offsets are excluded
   from the inventory's net figure too (`test_all_invalid_offsets_result_in_zero_deduction`).
3. **Given** the gross-vs-net distinction, **when** the inventory is inspected, **then**
   `TotalScope1/2/3Tonnes` (gross) and `TotalOffsetsTonnes`/`NetEmissionsTonnes` (net) are
   stored as separate columns on `GHGInventories`, never by mutating the gross figure in
   place — mirroring how biogenic CO2 is held apart from the GWP total (CLAUDE.md rule #2).
4. **Given** an offset attached to an emissions record, **when** formal inventory totals are
   computed, **then** it follows that parent's explicit `InventoryId`; offsets on unassigned
   records or another same-year inventory do not reduce this inventory's net result.

---

### SDO-NAT-15 · Ecosystem and Species are tenant-scoped through a real foreign key

**As a** platform operator
**I want** ecosystem and species tenant isolation to be structural, not conventional
**so that** a future endpoint cannot forget the `EntityId` filter and leak data across
tenants.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | System |
| **Diagram** | [UML 04 §Land & ecosystem — F1 note](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 06 §Tenant isolation](../diagrams/bpmn/06-nature-tracking.md) |
| **Code** | `backend/apps/ecosystem/models.py` · `Ecosystem.EntityId`, `Species.EntityId` (`ForeignKey`, `db_column="EntityId"`) · `backend/apps/ecosystem/views.py` (`TenantViewSetMixin`) |
| **Tests** | `backend/apps/ecosystem/tests/test_tenant_scope.py`, `backend/apps/land/tests/test_ecosystem_link_isolation.py` |
| **Linear** | `area:nat` · `type:spec` · `risk:schema` |

**Acceptance criteria**

1. **Given** `Ecosystem.EntityId`/`Species.EntityId` are real
   `ForeignKey("entities.Entities", on_delete=models.PROTECT, db_column="EntityId")`
   fields — not the plain `IntegerField` they were before this fix — **when**
   `EcosystemViewSet`/`SpeciesViewSet` use `TenantViewSetMixin.get_queryset()`, **then**
   rows are filtered structurally via the FK relation rather than by a hand-rolled per-view
   filter.
2. **Given** a row created by entity A, **when** entity B's authenticated user
   `GET`s `/api/ecosystems/`, **then** entity A's row is absent from the results
   (`test_ecosystem_not_visible_to_other_entity`).
3. **Given** `TenantViewSetMixin` also provides audit logging — a gap closed alongside this
   fix — **when** a record is created, **then** an `AuditLog` row is written with
   `Action == "Create"`, `TableName == "ecosystem"` (or `"species"`), matching `EntityId` —
   behaviour these viewsets previously had none of at all
   (`test_ecosystem_create_writes_audit_log`).

Link: [F1](../diagrams/FINDINGS.md#f1).

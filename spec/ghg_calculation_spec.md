# GHG Calculation Specification — SusDevOS

**Standard:** GHG Protocol Corporate Accounting and Reporting Standard (Revised Edition)
**Supplementary:** GHG Protocol Corporate Value Chain Standard (Scope 3), IPCC 2006 Guidelines for LULUCF, ISO 14064-1:2018

---

## 1. Fundamental Formula

All GHG emissions follow the activity-data × emission-factor pattern:

```
EmissionsAmount (kg CO2e) = QuantityCanonical × EmissionFactor (kg CO2e per canonical unit)
                          × GWP_factor (if gas-specific factors are used)
```

`EmissionsAmountTonnes = EmissionsAmount / 1000`

**Server-side only.** The `.save()` override on `EmissionsData` triggers all calculations. Client-submitted `EmissionsAmount` values are ignored and overwritten. This is enforced in the serializer `validate()` method.

---

## 2. Unit Conversion Pipeline

Activity data arrives in user-selected units. Before applying emission factors, quantities are converted to **canonical units** per physical dimension.

### Canonical units

| Dimension  | Canonical unit | Symbol |
|------------|---------------|--------|
| Energy     | kilojoule     | kJ     |
| Volume     | litre         | L      |
| Mass       | kilogram      | kg     |
| Distance   | kilometre     | km     |
| Area       | square metre  | m²     |
| Count      | unit          | unit   |
| Currency   | US dollar     | USD    |

### Conversion

```python
QuantityCanonical = QuantityOrCost × Units.ConversionFactor
# where Units.ConversionFactor converts from InputUnit to canonical unit
# e.g. kWh → kJ: ConversionFactor = 3600
#      tonne → kg: ConversionFactor = 1000
#      US gallon → L: ConversionFactor = 3.785411784
```

`QuantityCanonical` is stored on `EmissionsData` for auditability. Emission factors in the `EmissionFactors` table are always expressed per canonical unit (`InputUnitId` references the canonical unit for that activity type).

### Implementation

```python
# EmissionsData.save() — simplified
def save(self, *args, **kwargs):
    if self.InputUnitId and self.QuantityOrCost is not None:
        conversion = self.InputUnitId.ConversionFactor or Decimal('1')
        self.QuantityCanonical = self.QuantityOrCost * conversion
    self._compute_emissions()
    super().save(*args, **kwargs)
```

---

## 3. Scope 1 — Direct Emissions

### 3.1 Stationary Combustion

Applies to on-site fuel combustion (generators, boilers, furnaces).

```
EmissionsAmount (kg CO2e) = FuelConsumed (canonical) × EF_total (kg CO2e / canonical unit)
```

Where `EF_total` is the combined GWP-weighted factor:

```
EF_total = (CO2Factor × GWP_CO2)
         + (CH4Factor × GWP_CH4)
         + (N2OFactor × GWP_N2O)
```

GWP values come from the linked `GwpDatasets` record (default: IPCC AR6, 100-year):

| Gas         | AR6 GWP100 |
|-------------|-----------|
| CO2         | 1         |
| CH4 fossil  | 29.8      |
| CH4 biogenic| 27.9      |
| N2O         | 273       |
| SF6         | 25,200    |
| HFC-134a    | 1,530     |
| HFC-32      | 771       |
| HFC-125     | 3,740     |

**Biogenic CO2** from combustion of biomass/biofuels is calculated separately:

```
BiogenicCO2Amount (kg) = FuelConsumed (canonical) × BiogenicCO2FactorKg
```

This is stored in `EmissionsData.BiogenicCO2Amount` and **excluded** from `EmissionsAmount`. It is aggregated into `GHGInventories.TotalBiogenicCO2Tonnes` and reported as a memo item, not in the GWP-weighted total, per GHG Protocol Corporate Standard §9.

### 3.2 Mobile Combustion

Same formula as stationary combustion. `ActivityCategory` = `mobile_combustion`. Fuel type distinguishes petrol, diesel, LPG, CNG, etc.

### 3.3 Fugitive Emissions

Refrigerant gases (HFCs, HCFCs, SF6) use the mass-balance or screening method:

```
EmissionsAmount (kg CO2e) = RefrigerantLeakage (kg) × GWP_refrigerant
```

`GWP_refrigerant` is looked up from `GwpValues` by `GasSubtype` (e.g. `HFC-134a`). If a blend is used, the blended GWP is entered as a custom `EmissionFactor`.

---

## 4. Scope 2 — Purchased Energy (Dual Method)

GHG Protocol requires reporting **both** location-based and market-based methods for Scope 2. Both are stored on each `EmissionsData` record where `Scope = 2`.

### 4.1 Location-Based Method

Uses grid-average emission factor for the country/region:

```
EmissionsAmountLocationBased (kg CO2e) = ElectricityConsumed (kWh) × EFLocationBased (kg CO2e/kWh)
```

`EFLocationBased` source example: IEA 2023 grid factors, DEFRA 2024 UK grid (0.207 kg CO2e/kWh).

### 4.2 Market-Based Method

Uses contractual instruments: supplier-specific factors, renewable energy certificates (RECs/GOs), or residual mix:

```
EmissionsAmountMarketBased (kg CO2e) = ElectricityConsumed (kWh) × EFMarketBased (kg CO2e/kWh)
```

Hierarchy for `EFMarketBased` (GHG Protocol Scope 2 Guidance, in order of preference):
1. Supplier-specific emission rate from energy attribute certificates (EACs)
2. Bilateral contract rate (PPA with specified EF)
3. Default residual mix factor for country/region
4. Grid-average factor (fallback — same as location-based; disclosed in inventory)

If an entity holds 100% renewable EACs covering all consumption: `EFMarketBased = 0`, making `EmissionsAmountMarketBased = 0`.

### 4.3 Reporting Rule

`GHGInventories.TotalScope2LocationBasedTonnes` and `TotalScope2MarketBasedTonnes` are both computed and reported. The inventory narrative must state which method is used as the primary figure for target-setting and verification. Market-based is the default primary method (GHG Protocol Scope 2 Guidance).

### 4.4 Implementation

```python
# EmissionsData._compute_scope2()
if self.Scope == 2 and self.QuantityCanonical:
    qty = self.QuantityCanonical  # in kJ (canonical energy)
    # Convert kJ → kWh for EF lookup (EFs stored per kWh)
    kwh = qty / Decimal('3600')

    if self.EFLocationBased:
        lb_kg = kwh * self.EFLocationBased
        self.EmissionsAmountLocationBased = lb_kg
        self.EmissionsAmountLocationBasedTonnes = lb_kg / Decimal('1000')

    if self.EFMarketBased:
        mb_kg = kwh * self.EFMarketBased
        self.EmissionsAmountMarketBased = mb_kg
        self.EmissionsAmountMarketBasedTonnes = mb_kg / Decimal('1000')

    # Primary EmissionsAmount uses market-based if available, else location-based
    primary = self.EmissionsAmountMarketBased or self.EmissionsAmountLocationBased
    self.EmissionsAmount = primary
    self.EmissionsAmountTonnes = (primary or Decimal('0')) / Decimal('1000')
```

---

## 5. Scope 3 — Value Chain Emissions

### 5.1 Category Assignment

`EmissionsData.Scope3Category` stores the GHG Protocol category number (1–15). The `Scope3RelevanceAssessments` table must have a completed assessment (`IsRelevant=True`) for a given entity + year + category before emissions in that category can be included in a conformant GHG Protocol inventory.

### 5.2 Calculation Methods by Category

| Category | Preferred method | Notes |
|----------|-----------------|-------|
| 1 Purchased Goods & Services | Spend-based (USD × EF) or supplier-specific | Spend in USD converted at CanonicalUnit=USD |
| 3 Fuel & Energy Related | Activity-based (kWh × upstream EF) | Use IEA upstream EFs |
| 4 Upstream T&D | Distance-based (tonne-km × EF) | CanonicalUnit=km; weight in kg |
| 6 Business Travel | Distance-based (km × passenger EF by mode) | Flight EFs include radiative forcing multiplier option |
| 7 Employee Commuting | Distance-based per employee per mode | Survey-based activity data |
| 15 Investments | Portfolio-based (equity share × investee emissions) | Equity share % stored in Entities.OwnershipSharePercent |

For all categories, the core formula is unchanged: `QuantityCanonical × EF_total`.

### 5.3 Spend-Based Fallback

When primary data is unavailable, spend-based calculation applies:

```
Emissions (kg CO2e) = Spend (USD) × EF_spend (kg CO2e / USD)
```

`DataAvailability` on `Scope3RelevanceAssessments` flags which categories use this fallback. Spend-based data is assigned `DataQuality = 4` (Modelled) on `EmissionsData`.

### 5.4 Relevance Assessment Prerequisite

A `Scope3RelevanceAssessments` record with `IsRelevant=True` is required per category per year before the reporting engine includes that category in the Scope 3 total. Categories assessed as not relevant (`IsRelevant=False`) must have an `ExclusionReason`. The inventory report lists excluded categories with reasons per GHG Protocol Value Chain Standard §7.

---

## 6. IPCC LULUCF — Biomass Carbon Stock Change

Tree removals generate **biogenic CO2** from carbon stock loss, reported under LULUCF (Land Use, Land Use Change and Forestry) accounting. This is separate from GHG Protocol Scope 1/2/3 and is reported as a memo item.

### 6.1 IPCC Tier 1 — Default Biomass Expansion Factor (BEF) Method

**Step 1: Above-ground biomass (AGB)**

Using volume-based approach (when merchantable timber volume `VolumeM3` is known):

```
AGB (tonnes dry matter) = VolumeM3 × BasicWoodDensity (D) × BiomassExpansionFactor (BEF)
```

| Parameter | Description | IPCC defaults |
|-----------|-------------|--------------|
| D (BasicWoodDensity) | tonnes dry matter / m³ fresh volume | Tropical hardwood ≈ 0.60, softwood ≈ 0.45 (IPCC Table 4.13) |
| BEF (BiomassExpansionFactor) | converts merchantable volume to total AGB | Tropical ≈ 1.74, Temperate/Boreal ≈ 1.30 (IPCC Table 4.5) |

**Step 2: Below-ground biomass (BGB)**

```
BGB (tonnes dry matter) = AGB × RootToShootRatio (R)
```

| Forest type | IPCC default R (Table 4.4) |
|-------------|--------------------------|
| Tropical    | 0.37                     |
| Temperate   | 0.26                     |
| Boreal      | 0.23                     |
| Mangrove    | 0.37 (use tropical)      |

**Step 3: Total biomass per tree (then multiply by count)**

```
TotalBiomassTonnes = (AGB + BGB) × Count
```

**Step 4: Carbon stock**

```
CarbonStockTonnesC = TotalBiomassTonnes × CarbonFraction (CF)
```

IPCC default CF = **0.47** for all forest types. Species-specific values used at Tier 2.

**Step 5: CO2 equivalent**

```
CO2EquivalentTonnes = CarbonStockTonnesC × (44 / 12)   [= × 3.6667]
```

This is the biogenic CO2 released from living biomass. Stored in `TreeRemovalRemovedSpecies.CO2EquivalentTonnes`.

**Step 6: Total carbon stock loss (Tier 2/3 only)**

```
TotalCarbonStockLossTonnesCO2e = CO2EquivalentTonnes
                                + DeadOrganicMatterTonnesCO2e   (optional, Tier 2+)
                                + SoilCarbonTonnesCO2e          (optional, Tier 3)
```

### 6.2 IPCC Tier 2 — Country-Specific Parameters

Use country-specific BEF, D, and R values from national forest inventories instead of global IPCC defaults. `BiomassCalculationMethod = 2`. Same formula as Tier 1 but with national parameters stored on `Species`.

### 6.3 IPCC Tier 3 — Allometric Equations

Uses species-specific allometric regression equations (DBH-based):

```
AGB = a × DBH^b   [species-specific coefficients from peer-reviewed literature]
```

`BiomassCalculationMethod = 3`. `BiomassCalculationNotes` must cite the allometric study. Soil carbon disturbance (`SoilCarbonTonnesCO2e`) is only computed at this tier.

### 6.4 Manual Entry (Tier 4)

Pre-calculated carbon values entered directly. `BiomassCalculationMethod = 4`. `BiomassCalculationNotes` is mandatory — must document source and method. Used when a certified arborist report or project-level carbon assessment provides figures directly.

### 6.5 Reporting Treatment

LULUCF biogenic CO2 is **not** included in the entity's Scope 1 total under GHG Protocol Corporate Standard. It is:
- Summed into `GHGInventories.TotalBiogenicCO2Tonnes`
- Reported separately in the inventory as "biogenic CO2 from LULUCF"
- Disclosed in TNFD / TCFD reporting as a contextual metric

---

## 7. Restoration Sequestration

Sequestration from restoration activities is recorded as a negative LULUCF emission (carbon removal). It does **not** offset Scope 1/2/3 unless the entity holds verified carbon credits from a certified standard (VCS, Gold Standard). Without certification, it is reported as a memo item.

### 7.1 Cumulative Sequestration Formula

```
CumulativeSequestrationTonnesCO2e =
    AnnualSequestrationRateTonnesCO2ePerHa
    × AreaHectares
    × YearsEstablished
    × SurvivalEstimate          (proportion of planted trees surviving, 0–1)
    × (1 − LeakageDiscountPercent / 100)
```

| Variable | Source |
|----------|--------|
| `AnnualSequestrationRateTonnesCO2ePerHa` | IPCC Annex 3A.1 / national forest inventories / peer-reviewed literature. Stored on `Species` (default) or overridden per `RestorationSpecies`. |
| `AreaHectares` | Mapped area in `RestorationSpecies.AreaHectares` |
| `YearsEstablished` | Computed: `(ReportDate − EstablishedDate).years` — stored as `YearsEstablished` decimal for auditability |
| `SurvivalEstimate` | Project-level estimate (not yet in schema — add to `Restorations` model if needed); default 0.85 for tropical planting without monitoring data |
| `LeakageDiscountPercent` | 0–100%; typical 10–20% for community forestry per VCS VM0047. Default 0. |

### 7.2 Permanence Risk

`PermanenceRisk` (Low/Medium/High) is recorded but does not automatically discount sequestration — it requires project-level assessment. The risk level must be disclosed in the inventory report. High-permanence-risk sites should not be used to make net-zero claims.

### 7.3 Additionality

`AddionalityAssessment` (text field) documents whether the restoration would have occurred without project intervention. Required for any carbon credit claim. For informational reporting only (no additionality deduction is applied automatically).

---

## 8. GHG Inventory Totals Computation

`GHGInventories` cached totals are computed on-demand by the reporting engine and stored for performance. Totals are invalidated (set to NULL) whenever an `EmissionsData` record linked to the inventory is created, updated, or deleted.

### 8.1 Aggregation Query

```python
def compute_inventory_totals(inventory_id):
    records = EmissionsData.objects.filter(
        InventoryId=inventory_id,
        DeletedAt__isnull=True,
    )

    scope1 = records.filter(Scope=1).aggregate(
        total=Sum('EmissionsAmountTonnes')
    )['total'] or Decimal('0')

    scope2_lb = records.filter(Scope=2).aggregate(
        total=Sum('EmissionsAmountLocationBasedTonnes')
    )['total'] or Decimal('0')

    scope2_mb = records.filter(Scope=2).aggregate(
        total=Sum('EmissionsAmountMarketBasedTonnes')
    )['total'] or Decimal('0')

    scope3 = records.filter(Scope=3).aggregate(
        total=Sum('EmissionsAmountTonnes')
    )['total'] or Decimal('0')

    biogenic = records.aggregate(
        total=Sum('BiogenicCO2AmountTonnes')
    )['total'] or Decimal('0')

    offsets = EmissionsOffsets.objects.filter(
        InventoryId=inventory_id,
        DeletedAt__isnull=True,
    ).aggregate(total=Sum('OffsetAmountTonnes'))['total'] or Decimal('0')

    # Net = Scope1 + Scope2(market-based) + Scope3 − Offsets
    net = scope1 + scope2_mb + scope3 - offsets

    GHGInventories.objects.filter(InventoryId=inventory_id).update(
        TotalScope1Tonnes=scope1,
        TotalScope2LocationBasedTonnes=scope2_lb,
        TotalScope2MarketBasedTonnes=scope2_mb,
        TotalScope3Tonnes=scope3,
        TotalBiogenicCO2Tonnes=biogenic,
        TotalOffsetsAppliedTonnes=offsets,
        NetEmissionsTonnes=net,
        TotalsLastComputedAt=now(),
    )
```

### 8.2 Net Emissions Formula

```
NetEmissionsTonnes = TotalScope1Tonnes
                   + TotalScope2MarketBasedTonnes   (primary Scope 2 method)
                   + TotalScope3Tonnes
                   − TotalOffsetsAppliedTonnes
```

Offsets are only subtracted when `EmissionsOffsets.IsVerified=True` and the credit meets the entity's quality threshold. Unverified offsets are stored but excluded from `NetEmissions` until reviewed.

---

## 9. Organisational Boundary and Consolidation

### 9.1 ConsolidationApproach

Set on `Entities.ConsolidationApproach` (entity default) and overridable on `GHGInventories.ConsolidationApproach` (per period).

| Approach | Rule |
|----------|------|
| 1 — Equity Share | Include % of each project's emissions = `PartnerSharePercent` |
| 2 — Financial Control | Include 100% of projects where entity has financial control |
| 3 — Operational Control | Include 100% of projects where entity has operational control |

### 9.2 Equity Share Attribution

When consolidation approach is Equity Share:

```python
AttributableEmissions = ProjectEmissions × (PartnerSharePercent / 100)
```

`PartnerSharePercent` stored on `DevelopmentProjectPartners`. The reporting engine filters projects by partner membership and applies the share before summing into the inventory.

### 9.3 Subsidiary Emissions

For parent entities using Financial or Operational Control, subsidiary emissions are included 100%:

```python
# Pseudocode — reporting engine
subsidiaries = Entities.objects.filter(ParentEntityId=entity_id)
for sub in subsidiaries:
    include_all_emissions(sub)   # 100% regardless of ownership share
```

For Equity Share parents:
```python
include_proportional_emissions(sub, sub.OwnershipSharePercent)
```

### 9.4 Double-Counting Risk

`DevelopmentProjectPartners.IsDoubleCountingRisk` is set automatically when:
- A project has ≥ 2 partners, AND
- At least one partner uses a 100%-attribution approach (Financial/Operational Control)

The `DoubleCountingNotes` field must be completed before the inventory can be submitted for verification. Verifiers check this field as part of their boundary review.

---

## 10. Target Progress Calculation

### 10.1 Absolute Contraction

```
ReductionAchieved (%) = (BaselineEmissions − CurrentEmissions) / BaselineEmissions × 100
ProgressToTarget (%) = ReductionAchieved / TargetReductionPercent × 100
```

`MilestoneAchievementStatus`:
- OnTrack (1): `ProgressToTarget ≥ (YearsElapsed / TotalTargetYears × 100) − 5%`
- AtRisk (2): behind by 5–15%
- Achieved (3): `ReductionAchieved ≥ TargetReductionPercent`
- Missed (4): milestone year passed and target not achieved

### 10.2 Intensity-Based

```
CurrentIntensity = CurrentEmissions / OutputMetric
IntensityReduction (%) = (BaselineIntensity − CurrentIntensity) / BaselineIntensity × 100
```

`OutputMetric` (revenue, FTE, m², MWh produced) is entered manually per year. Units must match `Targets.IntensityMetric`.

### 10.3 ~~SBTi Sector Decarbonization Approach (SDA)~~ — REMOVED (out of scope)

> SDA is an SBTi-specific target methodology, removed in the nature/MRV + TNFD
> refocus (see CLAUDE.md § Product scope). Generic intensity targets remain
> supported via `Targets`/`TargetMilestones`; the sector-benchmark pathway logic
> is not built.

---

## 11. Data Quality and Verification

### 11.1 Data Quality Tiers

| Code | Label | Example |
|------|-------|---------|
| 1 | Measured | Utility invoices, meter readings |
| 2 | Calculated | Activity data × published EF |
| 3 | Estimated | Engineering estimates, proxy data |
| 4 | Modelled | Spend-based, LCA, simulation |

Stored on `EmissionsData.DataQuality`. The reporting engine flags inventories where a material share (>5% of total tCO2e) comes from DataQuality=3 or 4, requiring disclosure.

### 11.2 Verification Status

`GHGInventories.VerificationStatus`:

| Code | Status | Description |
|------|--------|-------------|
| 1 | Unverified | Default — no external review |
| 2 | Pending | Submitted to verifier |
| 3 | Verified (Limited Assurance) | ISO 14064-3 / ISAE 3410 limited |
| 4 | Verified (Reasonable Assurance) | ISO 14064-3 / ISAE 3410 reasonable |

Verified inventories (`Status ≥ 3`) are immutable. Edit attempts return HTTP 403. Only SuperAdmin can unlock via the dedicated `POST /api/inventories/{id}/unlock/` endpoint (requires reason, logged to AuditLog).

### 11.3 Emission Factor Library Quality

`EmissionFactors` in the library carry `ApplicableYear` and `CountryCode`. The reporting engine warns (not blocks) when a record uses an EF whose `ApplicableYear` is more than 3 years older than the reporting year, flagging it for update.

---

## 12. GWP Dataset Management

The system supports multiple GWP datasets (AR4, AR5, AR6) to allow comparison and to meet requirements of specific frameworks (some regulatory schemes still mandate AR4 or AR5).

The default dataset is configured via `DEFAULT_GWP_DATASET_ID` env var. Entities can override the default per GHG inventory via `GHGInventories` — currently stored implicitly through the `EFId`'s linked dataset. A future migration may add `GwpDatasetId` FK directly to `GHGInventories`.

**Seed data (0010_gwp_datasets.py):** IPCC AR6 100-year GWPs are seeded at deployment. AR5 and AR4 sets can be added via admin or management command.

---

## 13. Calculation Sequencing — EmissionsData.save()

```
1. Validate Scope (1, 2, or 3)
2. Validate Scope3Category if Scope == 3
3. Convert QuantityOrCost → QuantityCanonical (using InputUnitId.ConversionFactor)
4. Resolve EmissionFactor values:
   a. If EFId is set → copy CO2Factor, CH4Factor, N2OFactor, BiogenicCO2FactorKg from library
   b. Else use manually entered EmissionFactor as TotalKgCO2ePerUnit
5. Compute GWP-weighted total EF:
   EF_total = (CO2Factor × GWP_CO2) + (CH4Factor × GWP_CH4) + (N2OFactor × GWP_N2O)
6. If Scope == 1 or Scope == 3:
   EmissionsAmount = QuantityCanonical × EF_total
   EmissionsAmountTonnes = EmissionsAmount / 1000
7. If Scope == 2:
   Compute LocationBased and MarketBased amounts (see §4.4)
   Set EmissionsAmount = MarketBased if available, else LocationBased
8. Compute BiogenicCO2Amount = QuantityCanonical × BiogenicCO2FactorKg
   BiogenicCO2AmountTonnes = BiogenicCO2Amount / 1000
9. Invalidate linked GHGInventory totals (set TotalsLastComputedAt = NULL)
10. Save record
```

---

## 14. Known Limitations and Future Work

| Limitation | Mitigation | Future work |
|------------|------------|-------------|
| Spend-based Scope 3 EFs not seeded | Manual entry via admin | Add EEIO (Environmentally Extended Input-Output) dataset per region |
| Upstream T&D tonnage not linked | Manual entry | Link to logistics/supply chain module |
| Restoration survival rate not in schema | Hardcoded default 0.85 | Add `SurvivalEstimatePct` to `Restorations` model |
| Multi-year recalculation on EF update | Not supported | Add `recalculate_inventory` Celery task |
| Radiative forcing multiplier for aviation | Not in EF library | Add `RadiativeForcingMultiplier` to `EmissionFactors` |

# 04 — Nature & MRV Domain Model

Land, ecosystems, species, and the two carbon-flux processes: **tree removals**
(stock loss) and **restorations** (sequestration). This is the IPCC LULUCF /
TNFD side of the platform.


**Related user stories** — [Nature & MRV — SDO-NAT-01…15](../../stories/04-nature-mrv.md)

## Land & ecosystem

```mermaid
classDiagram
    direction TB

    class LandParcels {
        +LandParcelId: PK
        +EntityId: FK PROTECT
        +ParcelName
        +AreaHectares
        +BoundaryGeoJSON: JSONField - not PostGIS
        +LandUseType / Tenure
        +ParcelReference / PlanningReference
    }

    class Ecosystem {
        +EcosystemId: PK
        +EntityId: FK PROTECT, db_column EntityId
        +EcosystemName / Type
    }

    class Species {
        +SpeciesId: PK
        +EntityId: FK PROTECT, db_column EntityId
        +ScientificName / CommonName
        +IUCNStatus «LC..EX» / IUCNSyncedAt
        +GBIFKey / Kingdom / Family
        +IPCCForestType
        +BasicWoodDensity
        +BiomassExpansionFactor
        +RootToShootRatio / CarbonFraction
        +AnnualSequestrationRateTonnesCO2ePerHa
    }

    class LandParcelEcosystems { <<junction>> }
    class SpeciesLandParcels { <<junction>> }
    class EcosystemTags { <<junction>> }
    class SpeciesTags { <<junction>> }
    class LandParcelTags { <<junction>> }
    class LandParcelContacts { <<junction>> }
    class LandParcelDocuments { <<junction>> }
    class LandParcelImages { <<junction>> }
    class LandParcelLocations { <<junction>> }
    class LandParcelEntities { <<junction>> }

    class Entities

    Entities "1" --> "*" LandParcels
    LandParcels "1" --> "*" LandParcelEcosystems
    Ecosystem "1" --> "*" LandParcelEcosystems
    Species "1" --> "*" SpeciesLandParcels
    LandParcels "1" --> "*" SpeciesLandParcels
    Ecosystem "1" --> "*" EcosystemTags
    Species "1" --> "*" SpeciesTags
    LandParcels "1" --> "*" LandParcelTags
    LandParcels "1" --> "*" LandParcelContacts
    LandParcels "1" --> "*" LandParcelDocuments
    LandParcels "1" --> "*" LandParcelImages
    LandParcels "1" --> "*" LandParcelLocations
    LandParcels "1" --> "*" LandParcelEntities
```

> **✅ F1 · Tenant isolation — real foreign key — fixed 2026-08-21.**
> Both fields used to be declared as `EntityId = models.IntegerField(help_text="FK to
> entities.Entities")` (`apps/ecosystem/models.py:27,52`) rather than as a real `ForeignKey`.
> With no relation, `TenantViewSetMixin.get_queryset()` could not filter them, so those
> viewsets mixed in only `EntityScopeInitialMixin` and enforced scoping in their own
> `get_queryset()` — a new endpoint that forgot the filter would have returned **every
> tenant's** species and ecosystems, silently and with no exception raised.
> **Now:** both fields are `models.ForeignKey("entities.Entities", on_delete=models.PROTECT,
> db_column="EntityId")`. `db_column` keeps the existing column name, so migration
> `ecosystem/0004` is `AlterField` only — confirmed with `sqlmigrate` before applying, no
> rename or data migration. Both viewsets now use `TenantViewSetMixin`, making isolation
> structural rather than conventional, which also closed a gap nobody had flagged: neither
> viewset previously wrote any `AuditLog` entries or set `UpdatedBy` — they now do. Regression
> tests remain in place (`apps/ecosystem/tests/test_tenant_scope.py`,
> `apps/land/tests/test_ecosystem_link_isolation.py`).
> See [F1 in the findings register](../FINDINGS.md#f1).

## Tree removals — carbon stock loss

```mermaid
classDiagram
    direction TB

    class TreeRemovals {
        +TreeRemovalId: PK
        +EntityId: FK PROTECT
        +ProjectId: FK nullable
        +RemovalDate / RemovalReference
        +TotalTreesRemoved
        +TotalBiomassCarbon 🔒
        +HasMitigationPlan / MitigationNotes
    }

    class TreeRemovalRemovedSpecies {
        +TreeRemovalId: FK CASCADE
        +SpeciesId: FK CASCADE
        +Count / VolumeM3
        +BiomassCalculationMethod
        +AboveGroundBiomassTonnes 🔒
        +BelowGroundBiomassTonnes 🔒
        +TotalBiomassTonnes 🔒
        +CarbonStockTonnesC 🔒
        +CO2EquivalentTonnes 🔒
        +DeadOrganicMatterTonnesCO2e
        +SoilCarbonTonnesCO2e
        +TotalCarbonStockLossTonnesCO2e 🔒
    }

    class TreeRemovalAffectedSpecies {
        +TreeRemovalId: FK CASCADE
        +SpeciesId: FK CASCADE
        +Notes
    }

    class Species
    class TreeRemovalEcosystems { <<junction>> }
    class TreeRemovalLandParcels { <<junction>> }
    class TreeRemovalTags { <<junction>> }
    class TreeRemovalContacts { <<junction>> }
    class TreeRemovalDocuments { <<junction>> }
    class TreeRemovalImages { <<junction>> }
    class TreeRemovalEntities { <<junction>> }

    TreeRemovals "1" --> "*" TreeRemovalRemovedSpecies
    TreeRemovals "1" --> "*" TreeRemovalAffectedSpecies
    Species "1" --> "*" TreeRemovalRemovedSpecies
    Species "1" --> "*" TreeRemovalAffectedSpecies
    TreeRemovals "1" --> "*" TreeRemovalEcosystems
    TreeRemovals "1" --> "*" TreeRemovalLandParcels
    TreeRemovals "1" --> "*" TreeRemovalTags
    TreeRemovals "1" --> "*" TreeRemovalContacts
    TreeRemovals "1" --> "*" TreeRemovalDocuments
    TreeRemovals "1" --> "*" TreeRemovalImages
    TreeRemovals "1" --> "*" TreeRemovalEntities
```

The distinction between **removed** and **affected** species is the TNFD-relevant one:
removed species carry the biomass/carbon computation, affected species record ecological
impact without a carbon figure.

## Restorations — sequestration

```mermaid
classDiagram
    direction TB

    class Restorations {
        +RestorationId: PK
        +EntityId: FK PROTECT
        +RestorationName / RestorationReference
        +StartDate / CompletionDate
        +TotalAreaHectares / TotalTreesPlanted
        +EstimatedCarbonSequestrationTonnes 🔒
    }

    class RestorationSpecies {
        +RestorationId: FK CASCADE
        +SpeciesId: FK CASCADE
        +Count / SurvivalEstimate
        +AreaHectares
        +YearsEstablished 🔒
        +AnnualSequestrationRateTonnesCO2ePerHa
        +CumulativeSequestrationTonnesCO2e 🔒
        +SequestrationDataSource
        +PermanenceRisk
        +LeakageDiscountPercent
        +AdditionalityAssessment
    }

    class Species
    class RestorationEcosystems { <<junction>> }
    class RestorationLandParcels { <<junction>> }
    class RestorationDevelopmentProjects { <<junction>> }
    class RestorationLocations { <<junction>> }
    class RestorationTags { <<junction>> }
    class RestorationContacts { <<junction>> }
    class RestorationDocuments { <<junction>> }
    class RestorationImages { <<junction>> }
    class RestorationEntities { <<junction>> }

    Restorations "1" --> "*" RestorationSpecies
    Species "1" --> "*" RestorationSpecies
    Restorations "1" --> "*" RestorationEcosystems
    Restorations "1" --> "*" RestorationLandParcels
    Restorations "1" --> "*" RestorationDevelopmentProjects
    Restorations "1" --> "*" RestorationLocations
    Restorations "1" --> "*" RestorationTags
    Restorations "1" --> "*" RestorationContacts
    Restorations "1" --> "*" RestorationDocuments
    Restorations "1" --> "*" RestorationImages
    Restorations "1" --> "*" RestorationEntities
```

## Biomass carbon calculation

Both sides share the same IPCC LULUCF shape, implemented in
`apps/restorations/services.py`:

```mermaid
flowchart LR
    subgraph Removal["Tree removal — stock loss"]
        R1["Species row<br/>TreeCount, DBH, height"] --> R2["compute_removed_species_carbon()"]
        R2 --> R3["Above-ground biomass<br/>allometric or per-tree default"]
        R3 --> R4["Below-ground biomass<br/>× root-to-shoot ratio"]
        R4 --> R5["Carbon stock<br/>× carbon fraction"]
        R5 --> R6["CO₂e<br/>× 44/12"]
        R6 --> R7["recompute_tree_removal_total()<br/>_sum_lulucf()"]
    end

    subgraph Rest["Restoration — sequestration"]
        S1["Species row<br/>TreeCount, survival rate"] --> S2["compute_restoration_species_sequestration()"]
        S2 --> S3["_years_established()<br/>from planting date"]
        S3 --> S4["Annual growth increment<br/>× years × surviving trees"]
        S4 --> S5["Carbon stock → CO₂e"]
        S5 --> S6["recompute_restoration_total()"]
    end

    R7 --> TOT[("TreeRemovals.<br/>TotalBiomassCarbon")]
    S6 --> TOT2[("Restorations.<br/>EstimatedCarbonSequestrationTonnes")]

    style R2 fill:#fff3e0,stroke:#e65100,color:#000
    style S2 fill:#fff3e0,stroke:#e65100,color:#000
```

Species-level parameters resolve through `_param(species, attr, forest_default_key)`:
the species' own value when set, otherwise the IPCC default for its `IPCCForestType`.

## External species enrichment

`apps/ecosystem/integrations.py` reaches **GBIF** (taxonomy / occurrence) and **IUCN**
(Red List status) to populate `Species.IUCNStatus` and canonical naming. This is a
synchronous, user-triggered lookup at species-creation time — not a scheduled sync.

---
*Source: `backend/apps/land/models.py`, `backend/apps/ecosystem/models.py`,
`backend/apps/restorations/models.py`, `backend/apps/restorations/services.py`,
`backend/apps/ecosystem/integrations.py`*

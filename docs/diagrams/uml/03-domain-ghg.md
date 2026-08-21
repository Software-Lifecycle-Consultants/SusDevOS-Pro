# 03 — GHG Accounting Domain Model

The emissions core: reference data (units, factors, GWP), the inventory container,
the emissions records themselves, and the target/offset satellites.


**Related user stories** — [GHG accounting — SDO-GHG-01…13](../../stories/02-ghg-accounting.md) · [Inventory & assurance — SDO-INV-01…13](../../stories/03-inventory-assurance.md)

## Reference data — units, factors, GWP

```mermaid
classDiagram
    direction LR

    class GwpDatasets {
        +GwpDatasetId: PK
        +Name «e.g. IPCC AR6» / Version
        +Horizon «100»
        +PublishedYear / IsDefault
    }
    class GwpValues {
        +GwpValueId: PK
        +GwpDatasetId: FK PROTECT
        +Gas / Subtype
        +GwpFactor: Decimal
    }
    class Units {
        +UnitId: PK
        +UnitName / UnitSymbol
        +PhysicalDimension
        +CanonicalUnit / IsCanonical
        +ConversionFactor «to canonical unit»
    }
    class EmissionFactorSets {
        +SetId: PK
        +SetName «DEFRA, Climatiq, ...»
        +Publisher / Version
        +GeographicScope
        +ApplicableYear / IsActive
    }
    class EmissionFactors {
        +FactorId: PK
        +SetId: FK PROTECT
        +InputUnitId: FK PROTECT nullable
        +FactorValue: Decimal
    }

    GwpDatasets "1" --> "*" GwpValues
    EmissionFactorSets "1" --> "*" EmissionFactors
    Units "1" --> "*" EmissionFactors : InputUnitId
```

## Inventory and emissions records

```mermaid
classDiagram
    direction TB

    class GHGInventories {
        +InventoryId: PK
        +EntityId: FK PROTECT
        +ReportingYear / PeriodFrom / PeriodTo
        +BaselineYear
        +GwpDatasetId: FK PROTECT
        +ConsolidationApproach «1..3»
        +VerificationStatus «1..4»
        +VerifiedBy: FK Users SET_NULL
        --
        VerificationStatus >= 3 → immutable
    }

    class Scope3RelevanceAssessments {
        +InventoryId: FK CASCADE
        +EntityId: FK PROTECT
        +AssessmentId: PK
        +CategoryNumber «1..15»
        +IsRelevant
        +ExclusionReason / Notes
    }

    class EmissionsData {
        +EmissionsId: PK
        +EntityId: FK PROTECT
        +ProjectId / PhaseId: FK nullable
        +InventoryId: FK nullable
        +Scope: SmallInt «1|2|3»
        +Scope3Category: SmallInt nullable
        +QuantityOrCost: Decimal «client input»
        +InputUnitId: FK PROTECT
        +QuantityCanonical: Decimal 🔒
        +EmissionFactorId: FK
        +EmissionFactor: Decimal
        +GwpDatasetId: FK PROTECT
        +EmissionsAmount: Decimal 🔒
        +EmissionsAmountTonnes: Decimal 🔒
        +BiogenicCO2FactorKg: Decimal
        +BiogenicCO2AmountTonnes: Decimal 🔒
        +EFLocationBased / EFMarketBased
        +EmissionsAmountLocationBased 🔒
        +EmissionsAmountMarketBased 🔒
        +VerificationStatus: SmallInt
        +VerifiedBy: FK Users
    }

    class EmissionsDetails {
        +EmissionsId: FK CASCADE
        +EntityId: FK PROTECT
        +GwpDatasetId: FK PROTECT
        +Gas / GasAmount
    }

    class EmissionsOffsets {
        +OffsetId: PK
        +EmissionsId: FK CASCADE
        +EntityId: FK PROTECT
        +OffsetAmountTonnes
        +CreditSerialNumber
        +CreditRegistry «verra | gold_standard»
        +RegistryValidationStatus
        +RegistryValidatedAt
        +RegistryProjectName / Type / VintageYear
        +RegistryRetirementBeneficiary
    }

    class Entities
    class DevelopmentProjects
    class GwpDatasets
    class Units
    class EmissionFactors

    Entities "1" --> "*" GHGInventories
    GHGInventories "1" --> "*" Scope3RelevanceAssessments
    GHGInventories "1" --> "*" EmissionsData
    GwpDatasets "1" --> "*" GHGInventories
    GwpDatasets "1" --> "*" EmissionsData
    Entities "1" --> "*" EmissionsData
    DevelopmentProjects "1" --> "*" EmissionsData
    Units "1" --> "*" EmissionsData : InputUnitId
    EmissionFactors "1" --> "*" EmissionsData
    EmissionsData "1" --> "*" EmissionsDetails
    EmissionsData "1" --> "*" EmissionsOffsets
```

🔒 = **server-computed**. Client-submitted values for these fields are overwritten in
`EmissionsData.save()` → `compute_emissions()`. They are never trusted from the request body.

## Targets

```mermaid
classDiagram
    class Targets {
        +TargetId: PK
        +EntityId: FK PROTECT
        +BaselineYear / TargetYear
        +ReductionPercent
        +ValidationStatus: SmallInt
    }
    class TargetMilestones {
        +MilestoneId: PK
        +TargetId: FK CASCADE
        +EntityId: FK PROTECT
        +MilestoneYear
        +TargetEmissionsTonnes
        +ActualEmissionsTonnes «filled nightly»
        +IsAchieved / Notes
    }
    Targets "1" --> "*" TargetMilestones
```

Targets are **generic** reduction targets. Per `CLAUDE.md` there is deliberately no SBTi
validation, registry sync, or SBTi-specific tiering — `ValidationStatus` is an internal
review flag, not an external submission state.

`tasks.emissions.link_milestone_actuals` (nightly, 01:30) populates `ActualEmissionsTonnes` from
recorded emissions.

## Currency

```mermaid
classDiagram
    class ExchangeRates {
        +RateId: PK
        +FromCurrency / ToCurrency
        +Rate: Decimal
        +RateDate / Source
    }
```

Populated by `tasks.integrations.sync_ecb_fx_rates` (17:00 daily), with an
Open Exchange Rates task as an alternative source. Needed because spend-based Scope 3
factors are denominated per unit of currency.

---
*Source: `backend/apps/emissions/models.py`, `backend/apps/emissions/services.py`,
`backend/tasks/emissions.py`, `backend/tasks/integrations/fx.py`*

# 03 — GHG Accounting Domain Model

The emissions core: source observations, operational relationships, formal inventory
membership, calculation reference data, assurance provenance, targets, and offsets.

**Related user stories** — [GHG accounting — SDO-GHG-01…14](../../stories/02-ghg-accounting.md) · [Inventory & assurance — SDO-INV-01…14](../../stories/03-inventory-assurance.md) · [Nature & MRV — SDO-NAT-11…14](../../stories/04-nature-mrv.md)

**Linear traceability** — [SUS-19 · inventory contract](https://linear.app/susdevos/issue/SUS-19/cfi-002-make-ghg-inventory-creation-satisfy-its-data-contract) · [SUS-21 · source-field preservation](https://linear.app/susdevos/issue/SUS-21/cfi-001-stop-silently-discarding-emission-form-fields) · [SUS-22 · tenant ownership](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship) · [SUS-24 · assurance transition](https://linear.app/susdevos/issue/SUS-24/cfi-005-put-inventory-verification-behind-an-authorised-transition) · [SUS-25 · project/phase/inventory assignment](https://linear.app/susdevos/issue/SUS-25/cfi-008-connect-project-phases-and-inventory-assignment-end-to-end) · [SUS-31 · offset parent](https://linear.app/susdevos/issue/SUS-31/cfi-013-make-standalone-offset-creation-preserve-its-parent-emission) · [SUS-32 · registry result ownership](https://linear.app/susdevos/issue/SUS-32/cfi-014-prevent-clients-from-self-validating-carbon-offsets) · [SUS-33 · exact membership totals](https://linear.app/susdevos/issue/SUS-33/cfi-015-compute-formal-inventory-totals-from-explicit-inventory)

## Reference data — units, factors, GWP

```mermaid
classDiagram
    direction LR

    class GwpDatasets {
        +GwpDatasetId: PK
        +Name
        +Version
        +Horizon
        +PublishedYear
        +IsDefault
    }
    class GwpValues {
        +GwpValueId: PK
        +GwpDatasetId: FK PROTECT
        +Gas
        +Subtype
        +GwpFactor: Decimal
    }
    class Units {
        +UnitId: PK
        +UnitName
        +UnitSymbol
        +PhysicalDimension
        +CanonicalUnit
        +IsCanonical
        +ConversionFactor
    }
    class EmissionFactorSets {
        +SetId: PK
        +SetName
        +Publisher
        +Version
        +GeographicScope
        +ApplicableYear
        +IsActive
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

The backend can convert through `InputUnitId`, but the first-party form still supplies only
free-text `Unit`; the denominator/canonical-unit contract remains open in
[SUS-20](https://linear.app/susdevos/issue/SUS-20/cfi-003-define-and-enforce-the-canonical-emission-unitfactor-contract).

<a id="inventory-emissions-domain"></a>

## Inventory, project, emissions, and offsets

```mermaid
classDiagram
    direction TB

    class GHGInventories {
        +InventoryId: PK
        +EntityId: FK PROTECT
        +ReportingYear
        +ReportingPeriodFrom
        +ReportingPeriodTo
        +BaselineYear
        +GwpDatasetId: FK PROTECT
        +ConsolidationApproach
        +BoundaryNotes
        +VerificationStatus
        +VerifiedBy: FK Users SET_NULL
        +VerifiedAt
        +VerificationNotes
        +TotalScope1Tonnes
        +TotalScope2LocationTonnes
        +TotalScope2MarketTonnes
        +TotalScope3Tonnes
        +TotalOffsetsTonnes
        +NetEmissionsTonnes
        +TotalsLastComputedAt
    }

    class Scope3RelevanceAssessments {
        +AssessmentId: PK
        +InventoryId: FK CASCADE
        +EntityId: FK PROTECT
        +CategoryNumber
        +IsRelevant
        +ExclusionReason
        +Notes
    }

    class DevelopmentProjects {
        +ProjectId: PK
        +EntityId: FK PROTECT
        +ProjectName
        +ProjectReference
    }

    class ProjectPhases {
        +PhaseId: PK
        +EntityId: FK PROTECT
        +ProjectId: FK CASCADE
        +PhaseName
        +PhaseNumber
        +StartDate
        +EndDate
    }

    class EmissionsData {
        +EmissionsId: PK
        +EntityId: FK PROTECT
        +ProjectId: FK SET_NULL nullable
        +PhaseId: FK SET_NULL nullable
        +InventoryId: FK SET_NULL nullable
        +Title
        +ActivityDescription
        +SupplierName
        +ReportingPeriodFrom
        +ReportingPeriodTo
        +ReportingYear
        +Scope
        +Scope3Category
        +QuantityOrCost
        +Unit
        +InputUnitId: FK PROTECT nullable
        +QuantityCanonical: Decimal CALCULATED
        +EmissionFactorId: FK SET_NULL nullable
        +EmissionFactor
        +EmissionFactorSource
        +GwpDatasetId: FK PROTECT
        +Gas
        +GasSubtype
        +EmissionsAmount: Decimal CALCULATED
        +EmissionsAmountTonnes: Decimal CALCULATED
        +BiogenicCO2AmountTonnes: Decimal CALCULATED
        +EFLocationBased
        +EFMarketBased
        +EmissionsAmountLocationBased: Decimal CALCULATED
        +EmissionsAmountMarketBased: Decimal CALCULATED
        +VerificationStatus
        +VerifiedBy: FK Users SET_NULL
        +VerifiedAt
    }

    class EmissionsDetails {
        +DetailId: PK
        +EmissionsId: FK CASCADE
        +EntityId: FK PROTECT
        +GwpDatasetId: FK PROTECT
        +Gas
        +GasAmount
    }

    class EmissionsOffsets {
        +OffsetId: PK
        +EmissionsId: FK CASCADE
        +EntityId: FK PROTECT
        +OffsetAmountTonnes
        +CertificateNumber
        +CreditSerialNumber
        +CreditRegistry
        +RegistryValidationStatus: SERVER MANAGED
        +RegistryValidatedAt: SERVER MANAGED
        +RegistryProjectName: SERVER MANAGED
        +RegistryProjectType: SERVER MANAGED
        +RegistryVintageYear: SERVER MANAGED
        +RegistryRetirementBeneficiary: SERVER MANAGED
    }

    class Entities
    class GwpDatasets
    class Units
    class EmissionFactors

    Entities "1" --> "*" GHGInventories
    Entities "1" --> "*" DevelopmentProjects
    DevelopmentProjects "1" --> "*" ProjectPhases
    GHGInventories "1" --> "*" Scope3RelevanceAssessments
    GHGInventories "1" --> "*" EmissionsData : explicit InventoryId
    DevelopmentProjects "1" --> "*" EmissionsData : optional ProjectId
    ProjectPhases "1" --> "*" EmissionsData : optional PhaseId
    GwpDatasets "1" --> "*" GHGInventories
    GwpDatasets "1" --> "*" EmissionsData
    Entities "1" --> "*" EmissionsData
    Units "1" --> "*" EmissionsData : InputUnitId
    EmissionFactors "1" --> "*" EmissionsData
    EmissionsData "1" --> "*" EmissionsDetails
    EmissionsData "1" --> "*" EmissionsOffsets : immutable parent
```

Calculated emission fields are overwritten by `EmissionsData.save()` →
`compute_emissions()`. Inventory status/provenance/totals and offset registry results are
server-managed request fields: normal client mutation is rejected with HTTP 400 rather than
silently trusted. Every critical relationship is validated against the active request entity.

`InventoryId` is nullable because working records can exist before formal assignment. Once
assigned, it—not reporting year—is the authoritative membership boundary. Offsets inherit that
membership through their immutable parent emission.

<a id="ghg-field-lineage"></a>

## Field lineage

```mermaid
flowchart LR
    A["User observations<br/>period · supplier · context<br/>quantity · factor identity"] --> B["Validated request contract<br/>known keys · same tenant<br/>consistent project/phase/inventory"]
    B --> C[("EmissionsData source fields")]
    C --> D["Server calculation<br/>unit conversion · factor · GWP"]
    D --> E[("Calculated gross results")]
    C --> F[("Explicit InventoryId membership")]
    F --> G["Submit and verify recomputation"]
    H[("Offset identity claim")] --> I["Registry integration"]
    I --> J[("Server-owned registry evidence")]
    J --> G
    G --> K[("Frozen inventory totals<br/>verifier and audit provenance")]

    style B fill:#e3f2fd,stroke:#0d47a1,color:#000
    style E fill:#e8f5e9,stroke:#1b5e20,color:#000
    style J fill:#e8f5e9,stroke:#1b5e20,color:#000
    style K fill:#e8f5e9,stroke:#1b5e20,color:#000
```

## Targets

```mermaid
classDiagram
    class Targets {
        +TargetId: PK
        +EntityId: FK PROTECT
        +BaselineYear
        +TargetYear
        +ReductionPercent
        +ValidationStatus
    }
    class TargetMilestones {
        +MilestoneId: PK
        +TargetId: FK CASCADE
        +EntityId: FK PROTECT
        +MilestoneYear
        +TargetEmissionsTonnes
        +ActualEmissionsTonnes
        +IsAchieved
        +Notes
    }
    Targets "1" --> "*" TargetMilestones
```

Targets are generic reduction targets. There is deliberately no SBTi validation or registry
sync. `tasks.emissions.link_milestone_actuals` populates milestone actuals nightly from formal
inventory net totals.

## Currency

```mermaid
classDiagram
    class ExchangeRates {
        +RateId: PK
        +FromCurrency
        +ToCurrency
        +Rate
        +RateDate
        +Source
    }
```

FX sync populates reference rates, but spend-based emissions calculation does not yet consume
them; the domain diagram does not imply that missing join is implemented.

---
*Source: `backend/apps/emissions/models.py`, `backend/apps/emissions/serializers.py`,
`backend/apps/emissions/services.py`, `backend/apps/projects/models.py`,
`backend/tasks/emissions.py`, `backend/tasks/integrations/fx.py`*

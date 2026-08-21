# BPMN 03 — GHG Inventory Close & Verification

The annual reporting cycle: open an inventory, assess Scope 3 relevance, accumulate records,
close, verify, and lock.

## Annual inventory process

```mermaid
flowchart TB
    subgraph L1["👤 Manager — sustainability lead"]
        A([Reporting year begins]) --> B[POST /ghg-inventories/<br/>ReportingYear, period from/to]
        B --> C[Choose GwpDatasetId<br/>e.g. IPCC AR6 GWP100]
        C --> D[Choose ConsolidationApproach<br/>1 Equity / 2 Financial / 3 Operational]
        D --> E[Assess Scope 3 relevance<br/>categories 1-15]
    end

    subgraph L2["⚙️ System"]
        E --> F[("INSERT Scope3RelevanceAssessments<br/>one row per category")]
        F --> G[("GHGInventories<br/>VerificationStatus = 1 Unverified")]
    end

    subgraph L3["👤 Staff — throughout the year"]
        G -.-> H[Record emissions against<br/>InventoryId]
        H --> I[/"See BPMN 02 —<br/>emissions lifecycle"/]
        I --> J{"Reporting period<br/>ended?"}
        J -->|"No"| H
        J -->|"Yes"| K([Data collection closed])
    end

    subgraph L4["⚙️ System — nightly"]
        K -.-> L[/"recompute_stale_inventory_totals<br/>01:00 daily"/]
        L --> M[/"_compute_inventory_totals()<br/>sum by scope"/]
        M --> N[("Scope 1 / 2 / 3 totals<br/>written to inventory")]
    end

    subgraph L5["👤 Manager"]
        N -.-> O[Review totals vs prior year]
        O --> P{"Complete and<br/>defensible?"}
        P -->|"No"| Q[Reopen data collection]
        P -->|"Yes"| R[Submit for verification<br/>VerificationStatus = 2 Pending]
    end

    Q -.-> H

    subgraph L6["👤 Verifier — internal or third party"]
        R -.-> S{"Assurance<br/>type?"}
        S -->|"Internal"| T[Sign off<br/>VerificationStatus = 3]
        S -->|"External"| U[Third-party assurance<br/>VerificationStatus = 4]
        S -->|"Rejected"| V[Send back to Unverified = 1]
    end

    subgraph L7["⚙️ System — lock"]
        T --> W[("VerifiedBy, VerifiedAt recorded")]
        U --> W
        W --> X([🔒 Status >= 3<br/>PATCH/DELETE return 403])
    end

    V -.-> O

    style X fill:#e8f5e9,stroke:#1b5e20,color:#000
    style L fill:#fff3e0,stroke:#e65100,color:#000
```

The immutability check is a single comparison — `VerificationStatus >= 3` — so both the
first-party (3) and third-party (4) states are locked by the same guard. It is enforced in
the **view**, not the serializer.

## Scope 3 relevance assessment

GHG Protocol requires reporters to justify which of the 15 Scope 3 categories are material.
`Scope3RelevanceAssessments` is that record.

```mermaid
flowchart LR
    subgraph A1["👤 Manager"]
        A([For each of 15 categories]) --> B{"Relevant to<br/>this entity?"}
        B -->|"Yes"| C[Mark relevant<br/>+ plan data source]
        B -->|"No"| D[Mark not relevant<br/>+ MANDATORY justification]
    end

    subgraph A2["⚙️ System"]
        C --> E[("Scope3RelevanceAssessments<br/>IsRelevant = true")]
        D --> F[("Scope3RelevanceAssessments<br/>IsRelevant = false<br/>+ Justification text")]
        E --> G[/"Category expected in<br/>emissions data"/]
        F --> H[/"Exclusion documented<br/>for the assurance file"/]
    end

    subgraph A3["👤 Verifier"]
        G -.-> I{"Relevant categories<br/>actually populated?"}
        H -.-> J{"Exclusions<br/>defensible?"}
        I -->|"Gaps"| K([Query raised])
        J -->|"Weak"| K
        I -->|"Complete"| L([Proceed to sign-off])
        J -->|"Sound"| L
    end

    style K fill:#ffebee,stroke:#b71c1c,color:#000
    style L fill:#e8f5e9,stroke:#1b5e20,color:#000
```

The justification field is what makes an omitted category auditable rather than simply absent.

## Multi-entity consolidation

For a parent entity with subsidiaries, totals are consolidated by the chosen approach.

```mermaid
flowchart TB
    subgraph C1["👤 Manager — group level"]
        A([Group inventory needed]) --> B[Request consolidated totals]
    end

    subgraph C2["⚙️ System"]
        B --> C[/"compute_consolidated_emissions(<br/>entity, reporting_year, approach)"/]
        C --> D[/"accessible_entity_ids()<br/>walk ParentEntityId hierarchy"/]
        D --> E[/"_entity_scope_totals()<br/>per entity, per scope"/]
        E --> F{"Consolidation<br/>approach"}
        F -->|"1 Equity Share"| G[/"Weight by ownership %"/]
        F -->|"2 Financial Control"| H[/"Include 100% where<br/>financial control held"/]
        F -->|"3 Operational Control"| I[/"Include 100% where<br/>operational control held"/]
        G --> J[/"_round_scopes()"/]
        H --> J
        I --> J
        J --> K([Consolidated Scope 1/2/3 returned])
    end

    style K fill:#e8f5e9,stroke:#1b5e20,color:#000
```

`ConsolidationApproach` is stored on `Entities`, `DevelopmentProjects`, **and**
`GHGInventories` — the inventory's own value is the one that governs its reported figures,
allowing an entity to change approach between reporting years without rewriting history.

---
*Source: `backend/apps/emissions/models.py`, `backend/apps/emissions/views.py`,
`backend/apps/entities/services.py`, `backend/tasks/emissions.py`*

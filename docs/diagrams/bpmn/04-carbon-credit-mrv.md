# BPMN 04 — Carbon Credit MRV & Registry Validation

How a user-declared offset is tied to an emissions record, kept separate from gross emissions,
and promoted to registry evidence only by the integration path.

**Related user stories** — [Nature & MRV — SDO-NAT-11…14](../../stories/04-nature-mrv.md) · [Inventory & assurance — SDO-INV-04, 14](../../stories/03-inventory-assurance.md)

**Linear traceability** — [SUS-31 · preserve the parent emission](https://linear.app/susdevos/issue/SUS-31/cfi-013-make-standalone-offset-creation-preserve-its-parent-emission) · [SUS-32 · prevent client self-validation](https://linear.app/susdevos/issue/SUS-32/cfi-014-prevent-clients-from-self-validating-carbon-offsets) · [SUS-22 · tenant-owned relationships](https://linear.app/susdevos/issue/SUS-22/cfi-006-enforce-tenant-ownership-on-every-critical-relationship) · [SUS-33 · exact inventory membership](https://linear.app/susdevos/issue/SUS-33/cfi-015-compute-formal-inventory-totals-from-explicit-inventory)

<a id="offset-capture-validation"></a>

## Offset capture and validation

```mermaid
flowchart TB
    subgraph L1["👤 Manager / ESG consultant"]
        A([Credit evidence available]) --> B[Open offsets page or emission detail]
        B --> C[Select parent emission]
        C --> D[Enter title, provider, tonnes,<br/>registry, serial/certificate, validity dates]
        D --> E[POST standalone or nested offset route]
    end

    subgraph L2["⚙️ API — establish ownership and claim"]
        E --> F{"Parent supplied and<br/>owned by request entity?"}
        F -->|"No"| F1([400/404 and no write])
        F -->|"Yes"| G{"Parent record or inventory locked?"}
        G -->|"Yes"| G1([403 verified_immutable])
        G -->|"No"| H{"Client supplied registry<br/>result fields?"}
        H -->|"Yes"| H1([400 server-managed field])
        H -->|"No"| I[(EmissionsOffsets<br/>parent persisted<br/>status unverified)]
    end

    subgraph L3["⚙️ Nightly integration"]
        I -.-> J{"Registry?"}
        J -->|"Verra"| K[sync_verra_registry<br/>03:00]
        J -->|"Gold Standard"| L[sync_gold_standard_registry<br/>03:30]
        J -->|"No supported identity"| M([Remain unverified])
        K --> N{"Registry lookup conclusive?"}
        L --> N
        N -->|"Matched"| O[(status valid<br/>validated timestamp + evidence)]
        N -->|"Conclusive no match"| P[(status invalid<br/>validated timestamp)]
        N -->|"Unavailable / inconclusive"| Q([Keep prior status<br/>retry later])
    end

    subgraph L4["👤 Manager — correction"]
        P -.-> R[Investigate registry, serial,<br/>certificate, amount, or dates]
        R --> S[PATCH identity evidence]
    end

    S --> T[Clear all prior registry results<br/>reset status to unverified]
    T -.-> J

    style F1 fill:#ffebee,stroke:#b71c1c,color:#000
    style G1 fill:#ffebee,stroke:#b71c1c,color:#000
    style H1 fill:#ffebee,stroke:#b71c1c,color:#000
    style M fill:#fff3e0,stroke:#e65100,color:#000
    style P fill:#ffebee,stroke:#b71c1c,color:#000
    style Q fill:#fff3e0,stroke:#e65100,color:#000
    style O fill:#e8f5e9,stroke:#1b5e20,color:#000
```

The parent relationship is required on standalone creation, tenant-scoped, and immutable after
creation. Nested creation binds the parent from the URL. A user can declare a registry identity,
but cannot declare validation status, timestamp, project/vintage metadata, or beneficiary.

SUS-32 remains in progress because registry **claim depth** still needs hardening and complete
tests: the Verra path matches an exact serial, while the Gold Standard path currently proves a
project endpoint exists and does not yet establish every retirement/ownership assertion needed
for full assurance.

<a id="offset-failure-semantics"></a>

## Failure semantics

```mermaid
flowchart LR
    A([Sync task runs]) --> B{"Registry response usable?"}
    B -->|"Network/server failure"| C[Log, retry, or defer]
    B -->|"Empty/unparseable Verra CSV"| D[Abort entire run]
    C --> E([Do not downgrade any offset])
    D --> E
    B -->|"Usable"| F{"Identity matched?"}
    F -->|"Yes"| G([valid])
    F -->|"No"| H([invalid])

    style E fill:#fff3e0,stroke:#e65100,color:#000
    style G fill:#e8f5e9,stroke:#1b5e20,color:#000
    style H fill:#ffebee,stroke:#b71c1c,color:#000
```

An outage cannot masquerade as a fraudulent credit. `invalid` is written only after a usable,
registry-specific lookup produces a conclusive absence; unavailable or suspiciously empty data
leaves the prior status untouched.

<a id="offset-gross-net-boundary"></a>

## Where offsets sit relative to gross emissions

```mermaid
flowchart LR
    A[(EmissionsData<br/>gross EmissionsAmountTonnes)] --> B[Gross Scope totals]
    C[(EmissionsOffsets<br/>through parent EmissionsId)] --> D{"Parent InventoryId equals<br/>this formal inventory?"}
    D -->|"No"| E[Excluded]
    D -->|"Yes"| F{"Server validation status valid?"}
    F -->|"No"| E
    F -->|"Yes"| G[TotalOffsetsTonnes]
    B --> H[Gross position]
    G --> I[Net = gross − valid offsets]
    H --> I

    style A fill:#e3f2fd,stroke:#0d47a1,color:#000
    style C fill:#e8f5e9,stroke:#1b5e20,color:#000
    style E fill:#fff3e0,stroke:#e65100,color:#000
```

Offsets never mutate `EmissionsAmount`. They appear separately in formal inventory totals, and
only when their immutable parent emission is an explicit member of that inventory. Unassigned
or other same-year records cannot reduce the inventory's net figure.

## Scope boundary

MRV here means Verra / Gold Standard registry validation for the implemented product mandate.
There is no implied SBTi target validation, CDP export, NDC tagging, or RE100 workflow.

---
*Source: `frontend/src/app/(app)/offsets/page.tsx`,
`backend/apps/emissions/models.py`, `backend/apps/emissions/serializers.py`,
`backend/apps/emissions/views.py`, `backend/tasks/integrations/verra.py`,
`backend/tasks/integrations/gold_standard.py`, `backend/tasks/emissions.py`*

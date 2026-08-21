# BPMN 04 — Carbon Credit MRV & Registry Validation

How an offset claim is captured and then independently validated against the Verra or
Gold Standard registry. This is the MRV assurance loop.

## Offset capture and validation

```mermaid
flowchart TB
    subgraph L1["👤 Manager / ESG consultant"]
        A([Credits purchased or retired]) --> B[Open the emissions record<br/>the offset applies to]
        B --> C[POST /emissions/id/offsets/<br/>title, provider, tonnes]
        C --> D{"Credit serial<br/>available?"}
        D -->|"Yes"| E[Enter CreditSerialNumber<br/>+ CreditRegistry]
        D -->|"No"| F[Leave blank —<br/>unverified claim]
    end

    subgraph L2["⚙️ System — on save"]
        E --> G[("EmissionsOffsets<br/>RegistryValidationStatus = pending")]
        F --> H[("EmissionsOffsets<br/>RegistryValidationStatus = unverified")]
        G --> I[/"Awaits next registry sync"/]
        H --> J[/"Never validated —<br/>flagged in reporting"/]
    end

    subgraph L3["⚙️ Celery — integrations queue, nightly"]
        I -.-> K{"Which<br/>registry?"}
        K -->|"verra"| L[/"sync_verra_registry<br/>03:00 daily"/]
        K -->|"gold_standard"| M[/"sync_gold_standard_registry<br/>03:30 daily"/]
    end

    subgraph L4["🌍 Verra VCS registry"]
        L --> N[/"Stream ~500 MB CSV<br/>timeout 120s"/]
        N --> O{"Download<br/>succeeded?"}
        O -->|"No"| P([Log + abort —<br/>offsets stay pending])
        O -->|"Yes"| Q[/"Build set of valid serials<br/>+ retired serial → beneficiary map"/]
    end

    subgraph L5["⚙️ System — reconcile"]
        Q --> R{"Offset serial<br/>in registry?"}
        M --> R
        R -->|"Match"| S[("RegistryValidationStatus = valid<br/>RegistryValidatedAt = now")]
        R -->|"No match"| T[("RegistryValidationStatus = invalid")]
        S --> U[/"Backfill RegistryProjectName,<br/>ProjectType, VintageYear,<br/>RetirementBeneficiary"/]
    end

    subgraph L6["👤 Manager"]
        U -.-> V([✅ Offset evidenced])
        T -.-> W[Investigate — typo,<br/>wrong registry, or bad credit]
        W --> X[Correct serial → back to pending]
    end

    X -.-> I

    style P fill:#ffebee,stroke:#b71c1c,color:#000
    style T fill:#ffebee,stroke:#b71c1c,color:#000
    style V fill:#e8f5e9,stroke:#1b5e20,color:#000
    style J fill:#fff3e0,stroke:#e65100,color:#000
```

**Design property worth noting in review:** validation is *asynchronous and external*. A
user can never mark their own credit valid — only a registry match sets `valid`. That is what
makes the offset column defensible in an assurance context.

## Failure semantics

```mermaid
flowchart LR
    A([Sync task runs]) --> B{"Registry<br/>reachable?"}
    B -->|"No — RequestException"| C[/"Log error, abort run"/]
    C --> D([Offsets keep prior status<br/>no false 'invalid'])
    B -->|"Yes"| E{"Serial found?"}
    E -->|"Yes"| F([valid])
    E -->|"No"| G([invalid])

    style D fill:#fff3e0,stroke:#e65100,color:#000
    style F fill:#e8f5e9,stroke:#1b5e20,color:#000
    style G fill:#ffebee,stroke:#b71c1c,color:#000
```

An unreachable registry deliberately does **not** downgrade offsets to `invalid` — a network
outage must not look like a fraudulent credit. Status only moves to `invalid` on a successful
download where the serial is genuinely absent.

## Where offsets sit relative to gross emissions

```mermaid
flowchart LR
    subgraph Gross["Gross emissions — never reduced by offsets"]
        A[("EmissionsData<br/>EmissionsAmountTonnes")]
    end
    subgraph Offset["Offset register — reported separately"]
        B[("EmissionsOffsets<br/>OffsetAmountTonnes")]
    end
    subgraph Report["Reporting"]
        C[/"Gross emissions"/]
        D[/"Offsets applied"/]
        E[/"Net position"/]
    end

    A --> C
    B --> D
    C --> E
    D --> E

    style A fill:#e3f2fd,stroke:#0d47a1,color:#000
    style B fill:#e8f5e9,stroke:#1b5e20,color:#000
```

Offsets are a **separate table joined to** the emissions record, not a deduction applied to
`EmissionsAmount`. Gross emissions stay gross — GHG Protocol requires offsets to be reported
separately rather than netted into the inventory total. This mirrors the biogenic CO₂
treatment in `EmissionsData`, where the biogenic figure is likewise held apart from the
GWP total.

## Scope boundary

Per `CLAUDE.md`, MRV here means **Verra / Gold Standard credit validation** only. There is
deliberately no SBTi target validation, no CDP questionnaire export, and no NDC tagging —
if a spec document describes those, the document is stale, not a backlog item.

---
*Source: `backend/apps/emissions/models.py`, `backend/tasks/integrations/verra.py`,
`backend/tasks/integrations/gold_standard.py`, `backend/config/celery.py`*

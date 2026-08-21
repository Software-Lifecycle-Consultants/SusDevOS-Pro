# BPMN 02 — Emissions Data Lifecycle

From activity data capture to a locked, verified record — including the correction path.

## Main process

```mermaid
flowchart TB
    subgraph L1["👤 Staff — data contributor"]
        A([Activity data available<br/>fuel, electricity, travel, spend]) --> B[Open /emissions — new record]
        B --> C[Enter Scope, quantity,<br/>input unit, activity description]
        C --> D{"Scope?"}
        D -->|"Scope 1"| E[Select emission factor]
        D -->|"Scope 2"| F[Supply EFLocationBased<br/>AND EFMarketBased]
        D -->|"Scope 3"| G[Select category 1-15<br/>+ factor]
        E --> H[Submit POST /api/emissions/]
        F --> H
        G --> H
    end

    subgraph L2["⚙️ System — server-side only"]
        H --> I{"Feature gate<br/>is_feature_enabled()"}
        I -->|"Denied"| J([402 feature_gated<br/>upgrade modal])
        I -->|"Allowed"| K[/"Force EntityId = request.entity_id<br/>CreatedBy = request.user"/]
        K --> L[/"EmissionsData.save()<br/>compute_emissions()"/]
        L --> M[/"Unit conversion<br/>QuantityCanonical"/]
        M --> N[/"GWP lookup<br/>GwpValues by gas"/]
        N --> O[/"kg CO2e = qty x EF x GWP100"/]
        O --> P{"Biogenic factor<br/>present?"}
        P -->|"Yes"| Q[/"BiogenicCO2AmountTonnes<br/>EXCLUDED from total"/]
        P -->|"No"| R
        Q --> R{"Scope 2?"}
        R -->|"Yes"| S[/"Compute BOTH location-based<br/>and market-based amounts"/]
        R -->|"No"| T
        S --> T[("INSERT emissions_data")]
        T --> U[("AuditLog: Create")]
        U --> V[/"Client-submitted EmissionsAmount<br/>is discarded"/]
    end

    subgraph L3["👤 Manager — verifier"]
        V -.-> W[Reviews record on /emissions/id]
        W --> X{"Data<br/>defensible?"}
        X -->|"No"| Y[Request correction]
        X -->|"Yes"| Z[POST /emissions/id/verify/]
    end

    subgraph L4["⚙️ System — verification"]
        Z --> AA[/"verify_record()<br/>VerificationStatus = 3"/]
        AA --> AB[("VerifiedBy, VerifiedAt,<br/>VerificationNotes")]
        AB --> AC[("Notification:<br/>emissions_verified")]
        AC --> AD([🔒 Record locked<br/>PATCH/DELETE now 403])
    end

    Y -.-> C

    style J fill:#ffebee,stroke:#b71c1c,color:#000
    style V fill:#fff3e0,stroke:#e65100,color:#000
    style AD fill:#e8f5e9,stroke:#1b5e20,color:#000
```

**The controlling rule:** emissions are never computed on the client. `EmissionsAmount`,
`EmissionsAmountTonnes`, `QuantityCanonical`, `BiogenicCO2AmountTonnes`, and both Scope 2
amounts are populated by `compute_emissions()` inside `EmissionsData.save()`. Whatever the
client sends for those fields is overwritten.

## Correction path — unlocking a verified record

```mermaid
flowchart TB
    subgraph U1["👤 Staff / Manager"]
        A([Error found in a<br/>verified record]) --> B[Attempt edit]
        B --> C([403 — record is locked])
        C --> D[Escalate to SuperAdmin<br/>with justification]
    end

    subgraph U2["🛡️ SuperAdmin"]
        D -.-> E{"Correction<br/>justified?"}
        E -->|"No"| F([Refuse — record stands])
        E -->|"Yes"| G[POST /emissions/id/unlock/<br/>with mandatory reason]
    end

    subgraph U3["⚙️ System"]
        G --> H{"✅ F9 — IsSuperAdmin?<br/>enforced in the VIEW<br/>AND in unlock_record()"}
        H -->|"No"| I([403 denied])
        H -->|"Yes"| J[/"unlock_record()<br/>VerificationStatus = 1"/]
        J --> K[("AuditLog<br/>Action = Unlock_Verified<br/>RetentionTier = 3 → 7 years")]
        K --> L[("Notification:<br/>emissions_unlocked")]
        L --> M([Record editable again])
    end

    M -.-> N[Re-enter the main process<br/>at correction + re-verification]

    style C fill:#ffebee,stroke:#b71c1c,color:#000
    style I fill:#ffebee,stroke:#b71c1c,color:#000
    style K fill:#fff3e0,stroke:#e65100,color:#000
```

The 7-year audit entry is the compliance artefact: every unlock is permanently attributable
to a named SuperAdmin with a stated reason.

> **✅ F9 · Authorization — guard moved into the service — fixed 2026-08-21.**
> `unlock_record()` (`apps/emissions/services.py:169`) performed the privileged state change
> but checked nothing itself — its own docstring said *"Only callable by SuperAdmin — the view
> enforces that guard."* A management command, admin action or bulk-correction task could have
> unlocked verified records with no authorization check; the audit row would still be written,
> so the action stayed traceable, but it was never authorized.
> **Now:** `unlock_record()` raises `PermissionDenied` when `unlocked_by` is not a SuperAdmin,
> before any mutation or audit write, so a rejected unlock leaves no trace. The view's inline
> check is retained for its specific response body — the guard now lives in both places.
> See [F9 in the findings register](../FINDINGS.md#f9).

## Scope 2 dual-method detail

GHG Protocol Scope 2 Guidance requires both methods to be reported. The platform always
populates both columns, even when only one factor was supplied.

```mermaid
flowchart LR
    A([Scope 2 record saved]) --> B{"EFLocationBased<br/>supplied?"}
    B -->|"Yes"| C[/"LocationBased =<br/>qty x EFLocationBased"/]
    B -->|"No"| D[/"LocationBased =<br/>generic fallback result"/]
    C --> E{"EFMarketBased<br/>supplied?"}
    D --> E
    E -->|"Yes"| F[/"MarketBased =<br/>qty x EFMarketBased"/]
    E -->|"No"| G[/"MarketBased =<br/>LocationBased"/]
    F --> H[/"Primary EmissionsAmount<br/>= market-based"/]
    G --> H
    H --> I([Both columns always populated])

    style I fill:#e8f5e9,stroke:#1b5e20,color:#000
```

Both branches recompute on **every** save rather than only when the column is null — that
keeps re-saves idempotent instead of preserving a stale value from a previous save.

---
*Source: `backend/apps/emissions/views.py`, `backend/apps/emissions/services.py`,
`backend/apps/emissions/models.py`, `backend/apps/billing/mixins.py`*

# BPMN 01 — Tenant Onboarding & User Provisioning

From a prospect arriving on the marketing site to a fully provisioned user who can log in.

**Lanes** map to the four seeded roles: `SuperAdmin` (1), `Admin` (2), `Manager` (3),
`Staff` (4), plus the automated **System** lane.


**Related user stories** — [Tenancy & access — SDO-TEN-01, 02, 07](../../stories/01-tenancy-access.md) · [Billing — SDO-BIL-02](../../stories/06-billing-platform.md)

## Process

```mermaid
flowchart TB
    subgraph L1["🧑 Prospect / Public"]
        A([Arrives on marketing site]) --> B[Browses /pricing, /features]
        B --> C[Submits /register or /demo]
    end

    subgraph L2["⚙️ System — SignupView, AllowAny"]
        C -.-> G[Entity details entered by hand<br/>no external lookup on this path]
        G --> H[/"register_new_entity()"/]
        H --> I[("INSERT Entities")]
        I --> J[/"Attach free plan<br/>INSERT EntitySubscriptions"/]
        J --> K[("INSERT Users<br/>role = Admin")]
        K --> L[/"Generate onboard token<br/>PasswordResetTokens"/]
        L --> M[/"Send onboarding email"/]
        M --> N[("Notifications:<br/>entity_created, user_created")]
    end

    subgraph L3["👤 New Entity Admin"]
        M -.-> O[Opens emailed link<br/>/onboard]
        O --> P[Sets first password<br/>POST /auth/onboard]
        P --> Q([Can now log in])
    end

    subgraph L4["🛡️ SuperAdmin"]
        N -.-> R[Reviews new entity]
        R --> S{"Plan change<br/>needed?"}
        S -->|"Yes"| T[Adjust EntitySubscriptions]
        S -->|"No"| U([No action])
    end

    style H fill:#fff3e0,stroke:#e65100,color:#000
    style J fill:#e8f5e9,stroke:#1b5e20,color:#000
```

> **Correction (2026-08-21).** An earlier version of this diagram showed the Companies House
> lookup pre-filling entity details during self-service registration. **That flow does not
> exist.** `SignupView` is `AllowAny` and `register_new_entity()` never calls Companies House;
> `CompaniesHouseLookupView` (`apps/shared/urls_integrations.py:9`) requires `IsAuthenticated`,
> so an anonymous prospect cannot reach it. The lookup is available to an already-authenticated
> user maintaining entity details, not to a prospect signing up. The original was inferred from
> `spec/api_integrations.md` rather than read from the code — the drift that
> [SDO-GAP-10](../../stories/07-backlog-gaps.md#sdo-gap-10) is about.

**Ordering constraint.** `seed_plans` must have run before any entity is created —
`EntityCreateSerializer` looks up the free plan to attach a subscription, and entity creation
fails without it. This is why the seed sequence in the README is ordered
`seed_superadmins → seed_modules → seed_gwp → seed_plans` before any tenant exists.

## Sub-process: inviting additional users

```mermaid
flowchart TB
    subgraph M1["👤 Entity Admin"]
        A1([Needs a new team member]) --> A2[POST /users/<br/>email, role, designation]
    end

    subgraph M2["⚙️ System"]
        A2 --> B1{"Caller privileged?<br/>IsEntityAdmin"}
        B1 -->|"No"| B2([403 — denied])
        B1 -->|"Yes"| B3{"Seat limit<br/>in PlanFeatures?"}
        B3 -->|"Exceeded"| B4([402 — feature_gated])
        B3 -->|"Within limit"| B5[("INSERT Users<br/>EntityId = request.entity_id")]
        B5 --> B6[("INSERT UserRoles")]
        B6 --> B7[/"Generate onboard token"/]
        B7 --> B8[/"Email invite"/]
        B8 --> B9[("Notification: user_created")]
    end

    subgraph M3["👤 Invited user"]
        B8 -.-> C1[Opens /onboard link]
        C1 --> C2[Sets password]
        C2 --> C3([Active — privileges<br/>resolved from role])
    end

    subgraph M4["👤 Entity Admin — optional"]
        C3 -.-> D1{"Needs an<br/>exception?"}
        D1 -->|"Yes"| D2[Add UserPrivilegeOverrides<br/>Grant or Revoke]
        D1 -->|"No"| D3([Role privileges suffice])
        D2 --> D4[/"Overrides short-circuit<br/>role lookup entirely"/]
    end

    style B2 fill:#ffebee,stroke:#b71c1c,color:#000
    style B4 fill:#ffebee,stroke:#b71c1c,color:#000
    style D4 fill:#fff3e0,stroke:#e65100,color:#000
```

A user's `EntityId` is always taken from `request.entity_id`, never from the request body —
so an Admin cannot provision a user into somebody else's tenant.

## Sub-process: multi-entity access (ESG consultants)

```mermaid
flowchart LR
    subgraph N1["🛡️ SuperAdmin / Admin"]
        A([Consultant needs access<br/>to a second client]) --> B[Create EntityMembers row<br/>UserId + EntityId]
    end

    subgraph N2["⚙️ System — every later request"]
        B -.-> C[Request carries<br/>X-Entity-ID header]
        C --> D{"IsSuperAdmin?"}
        D -->|"Yes"| E[/"Any entity permitted"/]
        D -->|"No"| F{"user_can_access_entity()<br/>home entity or EntityMembers?"}
        F -->|"Yes"| G[/"request.entity_id set"/]
        F -->|"No"| H([403 forbidden_entity])
        E --> I[Queryset scoped to that entity]
        G --> I
    end

    style H fill:#ffebee,stroke:#b71c1c,color:#000
```

This is the mechanism that lets one consultant serve several client entities without
duplicate user accounts. Without an `X-Entity-ID` header the user falls back to their home
entity (`Users.EntityId`).

---
*Source: `backend/apps/entities/services.py`, `backend/apps/entities/middleware.py`,
`backend/apps/users/views.py`, `backend/apps/users/serializers.py`,
`backend/apps/billing/services.py`, `backend/apps/shared/permissions.py`*

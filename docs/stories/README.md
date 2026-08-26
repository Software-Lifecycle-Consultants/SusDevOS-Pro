# SusDevOS — User Stories

The behavioural specification of the platform, written from the user's side and traceable to
the code that implements it and the [diagram](../diagrams/README.md) that shows its mechanism.

Two kinds of story live here:

- **Built** — behaviour that exists today, verified by a test. These are a regression spec:
  if a story stops being true, something broke.
- **Gap** — known missing or undecided behaviour, in [07-backlog-gaps.md](07-backlog-gaps.md).
  These are the backlog.

Every story was derived by reading the code, not the `spec/` documents. Where a `spec/` file
describes something that does not exist, the story reflects the code and says so.

---

## Epics

| # | Epic | Stories | Covers |
|---|------|---------|--------|
| 01 | [Tenancy & access](01-tenancy-access.md) | `SDO-TEN-*` | Registration, auth, sessions, RBAC, multi-entity, audit |
| 02 | [GHG accounting](02-ghg-accounting.md) | `SDO-GHG-*` | Activity data capture, server-side calculation, factors, GWP |
| 03 | [Inventory & assurance](03-inventory-assurance.md) | `SDO-INV-*` | Inventories, Scope 3 relevance, verification, immutability, targets |
| 04 | [Nature & MRV](04-nature-mrv.md) | `SDO-NAT-*` | Land, ecosystems, species, removals, restoration, carbon credits |
| 05 | [Reporting & notifications](05-reporting-notifications.md) | `SDO-REP-*` | Async report jobs, downloads, notification inbox |
| 06 | [Billing & platform](06-billing-platform.md) | `SDO-BIL-*` | Plans, feature gates, usage, CMS, API contract |
| 07 | [Backlog & gaps](07-backlog-gaps.md) | `SDO-GAP-*` | Known gaps, undecided policy, drift risks |

---

## Conventions

### Story ID

`SDO-<AREA>-<nn>` — stable once assigned. **Never renumber**: diagrams, commits and Linear
issues reference these. Retire an ID rather than reusing it.

Areas: `TEN` · `GHG` · `INV` · `NAT` · `REP` · `BIL` · `GAP`

### Status vocabulary

| Status | Meaning |
|--------|---------|
| ✅ **Built** | Implemented and covered by a passing test |
| 🟡 **Partial** | Implemented, but an acceptance criterion is unmet or untested |
| ⬜ **Gap** | Not implemented — a backlog item |
| ❓ **Undecided** | Needs a product decision before it can be specified |

### Story shape

Each story carries a one-line user statement, a metadata block, and Given/When/Then
acceptance criteria written so they could be turned into tests without further interpretation.

```markdown
### SDO-GHG-02 · Emissions are computed by the server, never the client

**As a** sustainability contributor
**I want** the platform to calculate emissions from my activity data
**so that** the figure is defensible and consistent regardless of what my client sent.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Staff and above |
| **Diagram** | [UML 06 §6.2 — calculation sequence](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/apps/emissions/services.py` · `compute_emissions()` |
| **Tests** | `backend/apps/emissions/tests/test_api.py` |
| **Linear** | `area:ghg` · `type:spec` |

**Acceptance criteria**

1. **Given** a record submitted with `EmissionsAmount` set by the client,
   **when** it is saved,
   **then** that value is overwritten by the server-computed figure.
```

Rules for acceptance criteria:

- One observable behaviour per criterion — if it needs "and also", split it.
- Name the real field, endpoint, status code or table. `403` beats "an error".
- Criteria that encode a **rule** (an immutability lock, a gate, a formula) are the ones worth
  testing; criteria that restate CRUD are not. Prefer fewer, sharper ones.

### Roles

The four seeded roles, in ascending privilege: `Staff` · `Manager` · `Admin` · `SuperAdmin`.
"Manager and above" means the `IsManagerOrAbove` permission class, which also admits SuperAdmin.

---

## Traceability

Each story names its diagram and its code. Each diagram links back to the stories it realises.
That two-way link is the point of this package: a reviewer reading a sequence diagram can find
the requirement, and someone picking up a story can see the mechanism before touching code.

When a story is active work, its `Linear` row links to the issue and the affected diagram has a
`Linear traceability` line. The Linear issue, in turn, links back to both canonical documents.
This keeps requirements, mechanism, delivery state, and verification evidence navigable in
both directions.

| Epic | Primary diagrams |
|------|------------------|
| 01 Tenancy & access | [UML 02](../diagrams/uml/02-domain-tenancy-rbac.md) · [UML 06 §6.1](../diagrams/uml/06-sequences.md) · [BPMN 01](../diagrams/bpmn/01-tenant-onboarding.md) |
| 02 GHG accounting | [UML 03](../diagrams/uml/03-domain-ghg.md) · [UML 06 §6.2](../diagrams/uml/06-sequences.md) · [BPMN 02](../diagrams/bpmn/02-emissions-lifecycle.md) |
| 03 Inventory & assurance | [UML 03](../diagrams/uml/03-domain-ghg.md) · [UML 07](../diagrams/uml/07-state-machines.md) · [BPMN 03](../diagrams/bpmn/03-inventory-verification.md) |
| 04 Nature & MRV | [UML 04](../diagrams/uml/04-domain-nature-mrv.md) · [BPMN 04](../diagrams/bpmn/04-carbon-credit-mrv.md) · [BPMN 06](../diagrams/bpmn/06-nature-tracking.md) |
| 05 Reporting & notifications | [UML 06 §6.4](../diagrams/uml/06-sequences.md) · [UML 07](../diagrams/uml/07-state-machines.md) · [BPMN 05](../diagrams/bpmn/05-report-generation.md) |
| 06 Billing & platform | [UML 05](../diagrams/uml/05-domain-platform.md) · [UML 01](../diagrams/uml/01-component-architecture.md) · [UML 08](../diagrams/uml/08-async-topology.md) |

---

## Using these for change

The intended loop:

1. **A change starts as a story** — new behaviour gets a new ID, changed behaviour edits the
   existing one. The story is the statement of intent.
2. **The diagram is updated if the mechanism changed.** Not every story touches a diagram;
   one that alters a state machine, a sequence, or the domain model does.
3. **The acceptance criteria become the tests.** They are written to be transcribable.
4. **The commit references the story ID** — `feat(emissions): SDO-GHG-12 …` — so the history
   explains itself.

A story is done when its criteria pass and its status here says ✅ Built.

## Linear import

Stories are written to map onto Linear issues without rewriting.

| Story field | Linear field |
|-------------|--------------|
| `SDO-XXX-nn · Title` | Issue title |
| User statement + acceptance criteria | Description |
| Epic | Project, or a `Parent` issue |
| `Linear` row labels | Labels |
| Status | ⬜ Gap → `Backlog`; 🟡 Partial → `Todo`; ✅ Built → `Done` |
| Diagram + Code links | Description footer |

Suggested labels: `area:ten|ghg|inv|nat|rep|bil`, `type:spec|feature|bug|decision`,
`risk:schema|security|billing` where it applies.

> **Connected.** Workspace [susdevos](https://linear.app/susdevos), team `Susdevos`.
> The 13 actionable items — 11 gaps and 2 decisions — are imported as **SUS-5 … SUS-17**, each
> linking back to its story here, and each story carrying its Linear ID in the metadata block.
>
> The 83 ✅ Built and 🟡 Partial stories were deliberately **not** imported. They are a
> specification, not work: they belong in the repo beside the code they describe, where they are
> version-controlled and reviewed in the same pull request. Importing them would fill the
> backlog with issues nobody will action.
>
> When a story becomes work — new behaviour, or a Partial that needs its test — create the
> Linear issue then and add its ID to the story metadata row.

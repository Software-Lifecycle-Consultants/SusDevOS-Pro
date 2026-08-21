# SusDevOS — Architecture Diagram Set

Technical-review diagrams for the SusDevOS platform. Every diagram on these pages was
derived by reading the code in `backend/apps/`, `backend/tasks/`, `backend/config/` and
`frontend/src/` — **not** from `spec/`. Where the code and a spec document disagree, these
diagrams follow the code and the divergence is called out in a *Divergence* note.

All diagrams are Mermaid, embedded in Markdown. They render natively in GitHub, in the
VS Code Markdown preview, and in the published Artifact version. No tooling required.

---

## Contents

### Review findings

**[→ Findings register (F1–F10)](FINDINGS.md)** — every exception, divergence and open question
surfaced while deriving these diagrams, with the source line, the concrete failure scenario,
and the fix that was applied. **All ten are now resolved and verified against a running
stack.** Each is tagged `F1`–`F10` and annotated inline in the diagram where it is reachable,
so you can move between the register and the diagrams in either direction.

| ID | Finding | Resolution |
|----|---------|-----------------|
| [F1](FINDINGS.md#f1) | `Ecosystem` / `Species` scope by convention, not by FK | ✅ Real `ForeignKey` + `TenantViewSetMixin` |
| [F2](FINDINGS.md#f2) | Only the first active role is consulted | ✅ Union across all active roles |
| [F3](FINDINGS.md#f3) | No double-verification guard | ✅ Guard moved into the service |
| [F4](FINDINGS.md#f4) | `report_failed` sent before the retry | ✅ Deferred to the terminal attempt |
| [F5](FINDINGS.md#f5) | Gate returns 402, undocumented | ✅ `CLAUDE.md` corrected |
| [F6](FINDINGS.md#f6) | Tasks need an explicit import to register | ✅ `beat_init` validator + CI test |
| [F7](FINDINGS.md#f7) | Two tasks absent from `beat_schedule` | ✅ One scheduled, one confirmed intentional |
| [F8](FINDINGS.md#f8) | `past_due` loses features with no grace | ✅ Grace until `CurrentPeriodEnd` |
| [F9](FINDINGS.md#f9) | Unlock guard is in the view, not the service | ✅ Guard moved into the service |
| [F10](FINDINGS.md#f10) | `verify` was open to any authenticated user | ✅ Restricted to Manager+ |

All ten were verified against a running stack — `219 passed`, up from a `199` baseline before
the fixes. Two findings changed shape once investigated (F1 turned out cheaper than feared,
F2 less severe than originally written) and one, F8, had no live producer in this codebase —
see the [findings register](FINDINGS.md) for the full before/after detail on each.

### UML

| # | Diagram | Kind | What it answers |
|---|---------|------|-----------------|
| 01 | [Component & deployment architecture](uml/01-component-architecture.md) | Component | What processes exist, what they talk to, what is external |
| 02 | [Tenancy & RBAC domain](uml/02-domain-tenancy-rbac.md) | Class | How entities, users, roles and privileges relate |
| 03 | [GHG accounting domain](uml/03-domain-ghg.md) | Class | Inventories, emissions records, factors, GWP, targets, offsets |
| 04 | [Nature & MRV domain](uml/04-domain-nature-mrv.md) | Class | Land parcels, ecosystems, species, removals, restorations |
| 05 | [Platform services domain](uml/05-domain-platform.md) | Class | Billing, reports, notifications, audit, shared resources |
| 06 | [Request & calculation sequences](uml/06-sequences.md) | Sequence | Auth, tenant resolution, GHG calc, feature gate, report job |
| 07 | [State machines](uml/07-state-machines.md) | State | Verification, report job, credit validation, blog lifecycles |
| 08 | [Async task topology](uml/08-async-topology.md) | Component | Celery queues, beat schedule, external sync jobs |

### BPMN (swimlane process models)

| # | Process | Actors |
|---|---------|--------|
| 01 | [Tenant onboarding & user provisioning](bpmn/01-tenant-onboarding.md) | Prospect, SuperAdmin, Entity Admin, System |
| 02 | [Emissions data lifecycle](bpmn/02-emissions-lifecycle.md) | Contributor, System, Verifier, SuperAdmin |
| 03 | [GHG inventory close & verification](bpmn/03-inventory-verification.md) | Sustainability Manager, Verifier, System |
| 04 | [Carbon credit MRV & registry validation](bpmn/04-carbon-credit-mrv.md) | ESG Consultant, System, Verra/Gold Standard |
| 05 | [Report generation & delivery](bpmn/05-report-generation.md) | User, API, Celery worker, S3/MinIO |
| 06 | [Nature tracking — removals & restoration](bpmn/06-nature-tracking.md) | Project Manager, System, GBIF |

---

## Notation legend

### UML class diagrams

| Notation | Meaning |
|----------|---------|
| `A "1" --> "*" B` | One A relates to many B (Django `ForeignKey` from B to A) |
| `A "1" --> "1" B` | `OneToOneField` |
| `A ..> B` | Junction / association table between A and B |
| `<<abstract>>` | Django abstract base model — no table of its own |
| `<<junction>>` | Pure link table (composite key, no domain fields) |
| `PK` / `FK` | Primary / foreign key |
| `PROTECT` / `CASCADE` | The `on_delete` policy on that relationship |

### BPMN swimlanes

| Notation | BPMN element |
|----------|--------------|
| `([Rounded])` | Start / end event |
| `[Rectangle]` | Task / activity |
| `{Diamond}` | Exclusive gateway (decision) |
| `[/Parallelogram/]` | System-performed / automated task |
| `[(Cylinder)]` | Data store write |
| `-.->` | Message flow / async handoff between lanes |
| `subgraph` | Pool or lane (the actor performing the work) |

### Finding markers

| Notation | Meaning |
|----------|---------|
| `✅ Fn` inside a diagram | The node or transition where finding *n* was fixed |
| `> **✅ Fn · Category — fixed 2026-08-21.**` blockquote | The finding stated in full — what the problem was, and what the code does now — with a link to the register |
| `🔒` | Server-computed field — client-submitted values are overwritten |

---

## Scope note

The product is scoped to **nature / MRV + TNFD**. Per `CLAUDE.md`, these are deliberately
**not** built and therefore appear in no diagram: SBTi target validation, CDP export,
NDC tagging, RE100 renewable-commitment tracking. Generic GHG capabilities that happen to
support external frameworks (market-based Scope 2, for instance) are in scope and are modelled.

## Regenerating

These are hand-authored from source. When the domain model changes, the diagram to update
is the one whose *Source* footer names the file you touched — each diagram lists the exact
files it was derived from.

`atlas.html` in this folder is a generated single-page rendering of every document here —
open it directly in a browser to read all 54 diagrams with no Mermaid tooling installed. It is
built from the Markdown sources, so treat the `.md` files as authoritative and regenerate the
page rather than editing it.

## Viewing the diagrams

| Where | How |
|-------|-----|
| Browser, no setup | Open `atlas.html` |
| VS Code | Install `bierner.markdown-mermaid`, then `Ctrl+Shift+V` on any `.md` |
| GitHub | Renders Mermaid in Markdown natively — just open the file |
| Editing one diagram | Paste a single block into <https://mermaid.live> |

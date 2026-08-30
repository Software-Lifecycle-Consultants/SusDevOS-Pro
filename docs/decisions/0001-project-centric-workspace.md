# ADR 0001 — Project-centric workspace with hybrid domain ownership

**Status:** Proposed — design review required before implementation  
**Date:** 2026-08-30  
**Decision owner:** Product and engineering  
**Related stories:** [SDO-PRJ-01…08](../stories/08-project-workspace.md)  
**Target UML:** [Project-centric workspace](../diagrams/proposed/01-project-centric-workspace-uml.md)  
**Target BPMN:** [Project-centric user flows](../diagrams/proposed/02-project-centric-workspace-bpmn.md)

## Context

SusDevOS is used by development and restoration project managers, sustainability
managers, and ESG consultants. The current application exposes Projects, Emissions,
Inventories, Land Parcels, Ecosystems, Restorations, Targets, and Reports as peer-level
modules. That makes the portfolio visible, but it forces project managers to repeatedly
leave a project and reconstruct its context in other modules.

The data model deliberately has more than one valid boundary:

- `EntityId` is the tenant and organisational boundary.
- `InventoryId` is the formal GHG reporting and assurance boundary.
- `LandParcelId` is a durable spatial boundary for nature observations and impacts.
- `ProjectId` and `PhaseId` provide operational attribution for discrete work.

Making every record a child of a project would simplify navigation at the cost of
incorrect accounting. Ordinary corporate emissions can exist without a development
project; inventories can include several projects and non-project operations; a parcel
can be reused across projects; and project-impact accounting is not the same as observed
inventory accounting.

## Decision

SusDevOS will make **Project the primary operational workspace**, while retaining
**hybrid domain ownership**.

A project workspace is a read model and navigation context, not a new database owner.
It assembles canonical records through their existing explicit relationships. Creating
a record from the workspace preselects the project and applicable phase, but the API
continues to validate and store the canonical record in its existing domain.

### Authoritative boundaries

| Question | Authoritative boundary | Project's role |
|---|---|---|
| Which tenant owns the record? | `EntityId` | The selected project must belong to the same entity. |
| Which actual emissions are assured? | Explicit `InventoryId` membership | Project is an attribution/filter and cannot alter inventory membership. |
| Where did a nature condition or impact occur? | Land parcel/site | Projects link to the parcel; they do not own or duplicate it. |
| Which phase of work caused or used the record? | `ProjectId` + optional `PhaseId` | Project context is prefilled for project-originated capture. |
| What effect did an intervention have versus a baseline? | A future project-impact record | It must remain separate from observed inventory emissions. |
| Which credits were held or retired for a claim? | A future credit/retirement ledger | An internal or registry project may be referenced, but is not the ledger owner. |

### Immediate product rules

1. Entity remains the tenant and compliance root.
2. Formal inventory totals continue to use exact `InventoryId` membership.
3. A canonical record is stored once. Project views link or filter it; they never copy it.
4. Project-originated capture preselects the project. Phase choices are limited to that project.
5. Global or inventory-originated emissions may have no project without being treated as invalid.
6. Project summaries and reports include only explicitly attributed records. A formal report
   requires either a date range or an inventory whose dates become that range; nature values use
   the range end as their as-of date. An overview may default to **lifetime to date**, but must
   label that basis prominently.
7. Land parcels remain reusable entity assets and may be linked to more than one project.
8. Nature interventions require a land parcel. A project is preselected in project context but
   may be absent for entity-level land management initiated outside a project.
9. Making a project inactive must not delete emissions, inventories, parcels, ecosystem history,
   removals, restorations, evidence, or audit records.
10. Project-impact estimates, avoided emissions, inventory actuals, and credit claims are never
    silently netted together.
11. Operational emissions, tree-related biomass stock loss, restoration sequestration estimates,
    and attached offsets/credits remain separately labelled measures because their time bases and
    assurance meanings differ.
12. A restoration linked to several projects may appear in each project's detail view, but it
    must not be added repeatedly to portfolio totals without an approved allocation rule.
13. Changing project or phase attribution never changes `InventoryId`. Changing inventory
    membership never creates a project attribution.
14. First-slice capture assigns at most one project to a new nature event. Existing restorations
    linked to several projects remain visible as shared, non-additive records until allocation
    semantics are approved.

## Vocabulary

| Term | Meaning in SusDevOS |
|---|---|
| **Project** | A discrete internal body of development, restoration, or improvement work. |
| **Phase** | A time-bounded subdivision of one project. |
| **Inventory** | A versioned organisational and operational GHG boundary for a reporting period. |
| **Land parcel / site** | A durable physical location that can outlive and be reused by projects. |
| **Ecosystem type** | Reusable classification/reference data. |
| **Ecosystem occurrence/assessment** | A site- and time-specific observation of area, condition, and evidence; deferred schema. |
| **Actual emission** | Observed activity data calculated and optionally assigned to an inventory. |
| **Project impact** | A separately calculated change against a counterfactual baseline; deferred schema. |
| **Registry project** | An external Verra/Gold Standard project, distinct from an internal project. |
| **Credit/retirement** | A transferable unit and its use in a claim; deferred ledger schema. |

The UI will continue to use **Project** for the existing internal concept. Wherever external
credit metadata is shown, it must say **Registry project** to prevent conflation.

## First implementation slice — no schema migration

The first slice uses relationships and filters that already exist:

- Add a project workspace with Overview, Phases, Sites & Parcels, Emissions, Nature
  Interventions, and Reports sections.
- Aggregate project emissions through `EmissionsData.ProjectId` and phases through `PhaseId`.
- Surface project-linked land parcels through `DevelopmentProjectLandParcels`.
- Surface tree removals through `TreeRemovals.ProjectId` and restorations through
  `RestorationDevelopmentProjects`.
- Launch create flows from the workspace with project context preselected.
- Preserve global portfolio and inventory views.
- Show current offsets only through the project-attributed emissions to which they are attached;
  do not present the current child records as an independent credit ledger.
- Generate project reports only from an explicit `ProjectId` plus either a date range or an
  inventory; derive the nature as-of date from the range end and show included/excluded classes.

This slice does **not** require a universal `ProjectId`, a data backfill, or a project-owned
copy of any canonical record.

## Deferred schema decisions

These gaps are deliberately modelled so the first slice does not accidentally hard-code
around them. They require separate evidence and approval:

1. **Operational site/source.** Corporate emissions need a durable facility, source, meter,
   vehicle/fleet, or supplier context independent of projects.
2. **Ecosystem occurrence and observation history.** Area, condition, observation date,
   methodology, evidence, and species observations belong on dated parcel-specific assessments
   rather than a reusable ecosystem type or an undated junction.
3. **Project-impact accounting.** Baseline scenario, project scenario, leakage, additionality,
   monitored period, and calculated effect need a separate record from actual emissions.
4. **Scoped targets.** A target needs an explicit scope such as entity, inventory, or project;
   the existing entity-owned target must not be relabelled project-level without a relation.
5. **Credit ledger.** Credit lots, holdings, retirements, beneficiaries, and applications to
   claims should not remain conceptually attached to one arbitrary emissions row.
6. **Multi-project allocation.** If one emission or restoration genuinely serves several
   projects, add an allocation/primary-attribution rule with amount/percentage and method rather
   than duplicating or repeatedly summing the source record.
7. **Project lifecycle.** The inherited audit `Status` values are not a business lifecycle.
   Named states such as planned, active, completed, and archived need transition rules before
   they become product concepts.

## Alternatives considered

### Make Project the required parent of every operational record

Rejected. It creates synthetic “business as usual” projects, makes shared sites ambiguous,
couples project closure to assurance history, and conflates corporate inventory accounting
with intervention accounting.

### Keep all modules as peers and add only more filters

Rejected. It preserves accounting boundaries but does not solve the project manager's main
usability problem: assembling a coherent view of one body of work.

### Duplicate records into a project-specific store

Rejected. Two mutable copies would create reconciliation, audit, and double-counting risks.

## Consequences

### Positive

- Project managers get a coherent workspace and context-preserving create flows.
- Sustainability managers retain a correct entity/inventory workflow.
- Sites and nature history survive across the project lifecycle.
- The first slice is reversible and low migration risk.
- Future project-impact and credit-ledger work has an explicit boundary.

### Costs and risks

- Project pages become composed views across several APIs and need consistent loading/error states.
- Permission and tenant checks must be applied to every related collection.
- Project reports must disclose exclusions; a filter alone is not sufficient assurance evidence.
- A composed project page needs a declared time context; an unlabelled all-time total is unsafe.
- Shared restorations require attribution disclosure until an allocation model is approved.
- Existing models do not yet capture operational facilities or site-specific ecosystem assessments.
- Some existing marketing/user-guide language may need correction once the workflow is accepted.

## Design gate

No application code or database migration should implement this decision until all of the
following are true:

- [ ] Product accepts the authoritative-boundary table and vocabulary.
- [ ] The target UML is internally consistent and distinguishes existing from proposed records.
- [ ] The BPMN covers project-originated, inventory-originated, and site-originated capture.
- [ ] Every first-slice behavior has a user story with observable acceptance criteria.
- [ ] Project archive, cross-tenant, verified-inventory, and report-boundary exceptions are covered.
- [ ] Project report measures are separated by accounting meaning and shared-record handling is explicit.
- [ ] Deferred schema decisions are excluded from the first implementation estimate.

## References

- [GHG Protocol — Inventory and Project Accounting](https://ghgprotocol.org/blog/inventory-and-project-accounting)
- [GHG Protocol — Project Protocol](https://ghgprotocol.org/project-protocol)
- [TNFD — LEAP assessment guidance](https://tnfd.global/publication/additional-guidance-on-assessment-of-nature-related-issues-the-leap-approach/)
- Current domain diagrams: [GHG](../diagrams/uml/03-domain-ghg.md) and
  [Nature & MRV](../diagrams/uml/04-domain-nature-mrv.md)
- Current process diagrams: [Emissions lifecycle](../diagrams/bpmn/02-emissions-lifecycle.md),
  [Inventory verification](../diagrams/bpmn/03-inventory-verification.md), and
  [Nature tracking](../diagrams/bpmn/06-nature-tracking.md)

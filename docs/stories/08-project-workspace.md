# 08 — Project-Centric Workspace (Proposed)

These stories define the design contract for making a project the primary operational
workspace without making it the owner of every record. They describe intended behavior,
not current implementation. No story may be marked Built until its acceptance criteria
are covered by tests and the [design decision](../decisions/0001-project-centric-workspace.md)
has been accepted.

## Scope of the first slice

- Compose a project workspace from canonical project, phase, emissions, land-parcel,
  tree-removal, restoration, inventory-context, and report records.
- Preserve global emissions, inventory, land, and nature workflows.
- Prefill project context only when capture starts from a project.
- Use existing foreign keys and junctions; do not add a schema migration in this slice.
- Show the boundary and time basis for every project summary or report. A formal report accepts
  one date range or one inventory; the range end is the nature as-of date.

## Explicit exclusions

- A mandatory `ProjectId` on every operational record.
- A new operational-site/facility hierarchy.
- Parcel-specific ecosystem-occurrence or observation history.
- Counterfactual project-impact, additionality, or avoided-emissions accounting.
- Project-scoped targets, a carbon-credit ledger, or multi-project allocation records.
- A richer project lifecycle beyond the minimum non-destructive archive contract below.

Those concepts remain deferred in
[UML 01 § Deferred target](../diagrams/proposed/01-project-centric-workspace-uml.md#deferred-domain-extensions).
They must not be approximated with duplicated records, inferred relationships, or UI-only
labels during this slice.

## Vocabulary caveat

**Project** means the existing internal development/restoration/improvement project.
An external Verra or Gold Standard project must be labelled **Registry project**.
**Inventory** is an explicit GHG reporting and assurance boundary, not a project container.
**Land parcel** is the existing durable spatial record; an operational site/source remains a
deferred concept. Project attribution, inventory membership, and parcel location answer
different questions and must remain independent.

---

<a id="sdo-prj-01"></a>

### SDO-PRJ-01 · Use a project as a workspace over canonical records

**As a** project manager  
**I want** one workspace that assembles the records related to a selected project  
**so that** I can manage the work without creating a second copy of its emissions, parcels,
or nature records.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Project manager or another entity member with permission to view the project |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — project workspace and capture](../diagrams/proposed/02-project-centric-workspace-bpmn.md#project-workspace-and-capture) |
| **Code** | Not implemented — anticipated project-detail composition over the existing project, phase, emissions, land, restoration, and report APIs |
| **Tests** | Required before Built — tenant isolation, relationship inclusion, canonical identity, and boundary-label tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** a project in the user's active entity, **when** the user opens its workspace,
   **then** the response identifies that project as the selected context.
2. **Given** a canonical record explicitly related to that project through an existing
   foreign key or junction, **when** its applicable workspace section loads, **then** the
   record appears with its canonical identifier.
3. **Given** a canonical record with no explicit relationship to the selected project,
   **when** the workspace loads, **then** that record is not inferred into the project from
   entity ownership, date overlap, parcel proximity, or inventory membership alone.
4. **Given** the same record is opened from a global module and from the project workspace,
   **when** its identifiers are compared, **then** both views reference the same canonical
   record rather than project-owned copies.
5. **Given** a user requests a project from another entity, **when** any workspace section
   is loaded, **then** the project and its related collections are not found.
6. **Given** the workspace displays a count or quantity, **when** the user inspects it,
   **then** the UI states the relationship scope and either the selected period or an explicit
   `lifetime to date` basis.

---

<a id="sdo-prj-02"></a>

### SDO-PRJ-02 · Preserve project and phase context during emission capture

**As a** project manager  
**I want** an emission started from a project to retain that project and offer only valid
phases  
**so that** the activity is attributed correctly without repeated selection.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Entity member permitted to create emissions for the selected project |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — project workspace and capture](../diagrams/proposed/02-project-centric-workspace-bpmn.md#project-workspace-and-capture) |
| **Code** | Not implemented — anticipated project-aware entry into the existing emissions create flow and server-side project/phase validation |
| **Tests** | Required before Built — fixed-context, valid-phase, invalid-phase, optional-phase, and independent-inventory tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** emission capture starts inside a project workspace, **when** the form opens,
   **then** the selected project is prefilled and cannot be replaced in that flow.
2. **Given** the selected project has phases, **when** the phase control opens, **then** it
   lists only phases belonging to that project and active entity.
3. **Given** the user leaves phase empty, **when** a valid emission is saved, **then** its
   `ProjectId` is the selected project and its `PhaseId` is null.
4. **Given** a client submits a phase belonging to another project or entity, **when** the
   request is validated, **then** the request is rejected and no emission is created.
5. **Given** the user selects an inventory, **when** the emission is saved, **then** its
   `InventoryId` is exactly the selected inventory and is not inferred from the project.
6. **Given** the user does not select an inventory, **when** the emission is saved, **then**
   project attribution succeeds with a null `InventoryId`.

---

<a id="sdo-prj-03"></a>

### SDO-PRJ-03 · Keep global and inventory emission capture valid without a project

**As a** sustainability manager  
**I want** to record ordinary organisational emissions without inventing a project  
**so that** the inventory represents the real reporting boundary.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Entity member permitted to create emissions or manage an inventory |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — global and inventory capture](../diagrams/proposed/02-project-centric-workspace-bpmn.md#global-and-inventory-capture) |
| **Code** | Current support: nullable project and explicit inventory relationships exist; not implemented — proposed UX and guardrail coverage |
| **Tests** | Required before Built — null-project, explicit-inventory, optional-project, phase-clearing, and same-entity tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** capture starts from the global emissions flow, **when** the user leaves project
   empty and submits otherwise valid data, **then** the emission is saved with a null
   `ProjectId`.
2. **Given** capture starts from an inventory, **when** the user leaves project empty and
   submits otherwise valid data, **then** the emission is saved with that exact
   `InventoryId` and a null `ProjectId`.
3. **Given** an emission has a null `ProjectId`, **when** it appears in an inventory or
   global list, **then** it is not labelled invalid, incomplete, or an attribution error
   solely for lacking a project.
4. **Given** a project is selected in a global or inventory flow, **when** the phase control
   opens, **then** it lists only phases belonging to that selected project.
5. **Given** a selected project is cleared, **when** the form state updates, **then** any
   selected phase is also cleared before submission.
6. **Given** a project or phase belonging to another entity is submitted, **when** the
   request is validated, **then** the request is rejected without changing inventory
   membership.

---

<a id="sdo-prj-04"></a>

### SDO-PRJ-04 · Link entity-owned land parcels to projects without transferring ownership

**As a** land or project manager  
**I want** to link a durable parcel to each project that uses it  
**so that** location history survives individual projects and is not duplicated.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Entity member permitted to manage the project and land-parcel links |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — parcel and nature intervention](../diagrams/proposed/02-project-centric-workspace-bpmn.md#parcel-and-nature-intervention) |
| **Code** | Current support: entity-owned parcels and project/parcel junctions exist; not implemented — proposed project-workspace linking UX |
| **Tests** | Required before Built — link, unlink, reuse, canonical identity, and cross-tenant rejection tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** an entity-owned parcel and project in the same entity, **when** an authorised
   user links them, **then** one relationship is created without changing the parcel's
   `EntityId` or creating a second parcel.
2. **Given** the parcel is already linked to one project, **when** it is linked to another
   project in the same entity, **then** both projects reference the same parcel identifier.
3. **Given** an existing project/parcel link, **when** the user attempts to create the same
   link again, **then** no duplicate relationship is created.
4. **Given** an existing project/parcel link, **when** it is removed, **then** the parcel and
   its canonical nature records remain present in the entity.
5. **Given** the project and parcel belong to different entities, **when** a link is
   attempted, **then** the request is rejected and no junction is created.

---

<a id="sdo-prj-05"></a>

### SDO-PRJ-05 · Capture nature interventions from the parcel and preserve their provenance

**As a** project or land manager  
**I want** every removal or restoration tied to its physical parcel with source inputs
preserved  
**so that** calculated carbon values remain traceable to what was observed.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Entity member permitted to create tree-removal or restoration records |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — parcel and nature intervention](../diagrams/proposed/02-project-centric-workspace-bpmn.md#parcel-and-nature-intervention) |
| **Code** | Not implemented — anticipated context-preserving entry into existing land/restoration flows plus end-to-end provenance tests |
| **Tests** | Required before Built — required-parcel, context, round-trip source-data, server-calculation, and tenant-isolation tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** tree-removal or restoration capture starts from a project workspace, **when**
   the form opens, **then** the project is prefilled and a same-entity parcel linked to that
   project must be selected before submission.
2. **Given** nature-intervention capture starts from a parcel or entity land flow, **when**
   the form opens, **then** that parcel is fixed and project attribution may remain empty.
3. **Given** a new nature intervention is created in the first slice, **when** project
   attribution is supplied, **then** the form and request accept at most one project.
4. **Given** accepted source inputs are submitted for an intervention, **when** the saved
   record and its child source rows are read back, **then** every accepted input is present
   with its canonical normalized value and no form field has been silently dropped.
5. **Given** source inputs require a carbon calculation, **when** the record is saved,
   **then** the authoritative derived value is calculated server-side from the persisted
   inputs and the selected canonical calculation method.
6. **Given** the client supplies a derived total that disagrees with the server result,
   **when** the request is processed, **then** the client total is rejected or ignored as an
   authority and the response returns the server result.
7. **Given** a project, parcel, species, or other referenced source record belongs to a
   different entity, **when** the intervention is submitted, **then** the request is
   rejected and no intervention or child row is created.
8. **Given** a removal and a restoration occur on the same parcel, **when** their values are
   displayed, **then** stock loss and sequestration remain separate rather than being
   silently netted.

This story uses only provenance fields and source rows supported by the canonical
intervention records. A new ecosystem-occurrence/evidence schema remains excluded.

---

<a id="sdo-prj-06"></a>

### SDO-PRJ-06 · Report a project with an explicit boundary and non-additive metrics

**As a** sustainability manager or assurance reviewer  
**I want** a project report to state exactly what it includes and when it applies  
**so that** unlike quantities are not mistaken for one assured net-carbon result.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Entity member permitted to view the project and request reports |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — project reporting](../diagrams/proposed/02-project-centric-workspace-bpmn.md#project-reporting) |
| **Code** | Not implemented — anticipated bounded project-summary query and explicit project parameters in the existing report workflow |
| **Tests** | Required before Built — required-boundary, explicit-attribution, separation, shared-restoration, and report-metadata tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** a formal project report is requested, **when** neither a complete date range nor
   an inventory is supplied, **then** validation fails before a report job is created.
2. **Given** a bounded request, **when** it is processed, **then** the project is validated
   against the caller's active entity before related data is read.
3. **Given** a bounded project report, **when** records are selected, **then** only records
   with an explicit existing relationship to that project are included.
4. **Given** the report contains operational emissions, tree-removal carbon-stock loss,
   restoration sequestration, or credits attached to project emissions, **when** results
   are rendered, **then** each category is shown separately with its unit and time basis.
5. **Given** those categories are shown together, **when** the report presents its headline
   figures, **then** it does not subtract them into an unqualified `net project carbon`
   value.
6. **Given** a restoration is linked to more than one project and no approved allocation
   record exists, **when** it appears in a project report, **then** it is marked as shared
   and the report discloses the risk of double counting across projects.
7. **Given** a report includes a shared restoration without an allocation method, **when** a
   cross-project roll-up is shown, **then** that roll-up is labelled non-additive rather
   than represented as double-count-free.
8. **Given** report generation completes, **when** the user reads its boundary statement,
   **then** it identifies the project, date range, nature as-of date, included relationship
   types, and known exclusions used for that report.

---

<a id="sdo-prj-07"></a>

### SDO-PRJ-07 · Keep verified inventory membership independent and immutable

**As an** assurance reviewer  
**I want** project actions to leave the exact verified inventory boundary unchanged  
**so that** a navigational improvement cannot rewrite assured evidence.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Sustainability manager, verifier, or project manager according to existing permissions |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — global and inventory capture](../diagrams/proposed/02-project-centric-workspace-bpmn.md#global-and-inventory-capture) |
| **Code** | Current support: explicit `InventoryId` membership and verified-record protections exist; not implemented — project-workspace regression coverage |
| **Tests** | Required before Built — exact membership, verified immutability, null-project verification, archive, and unlock-path tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** an emission belongs to an inventory, **when** its project or phase attribution
   changes through an allowed unverified workflow, **then** its `InventoryId` remains
   unchanged.
2. **Given** an emission does not belong to an inventory, **when** it receives project or
   phase attribution, **then** no `InventoryId` is inferred or added.
3. **Given** an inventory is verified, **when** a user attempts to edit or delete one of its
   member emissions from a project workspace, **then** the operation is blocked by the
   existing verified-inventory lock.
4. **Given** a verified inventory contains an emission with no project, **when** inventory
   totals are calculated, **then** that member remains included by its explicit
   `InventoryId`.
5. **Given** a project is archived or a project/parcel link is removed, **when** inventory
   membership is inspected, **then** no emission is removed from or added to an inventory.
6. **Given** an authorised inventory unlock occurs through the existing audited workflow,
   **when** a formerly locked member is corrected, **then** that workflow records the
   correction without treating project attribution as the inventory boundary.

---

<a id="sdo-prj-08"></a>

### SDO-PRJ-08 · Archive a project without erasing its history

**As a** project owner or auditor  
**I want** a completed or inactive project archived non-destructively  
**so that** its operational workspace stops accepting new work while its evidence remains
available.

| | |
|---|---|
| **Status** | 🟣 Proposed |
| **Role** | Project owner or entity administrator for archive; authorised members for read access |
| **Decision** | [ADR 0001 — project-centric workspace](../decisions/0001-project-centric-workspace.md) |
| **Diagram** | [UML — immediate hybrid domain](../diagrams/proposed/01-project-centric-workspace-uml.md#immediate-hybrid-domain) · [BPMN — archive and history](../diagrams/proposed/02-project-centric-workspace-bpmn.md#archive-and-history) |
| **Code** | Not implemented — anticipated non-destructive archive guard and read-only project-workspace state using an approved existing status representation |
| **Tests** | Required before Built — archive permission, read-only UI/API, relationship preservation, canonical-history, and inventory-lock tests |
| **Linear** | Not created — design review gate |

**Acceptance criteria**

1. **Given** an authorised user archives an active project, **when** the operation
   completes, **then** the project remains stored with the same identifier and is available
   through an explicit archived-project view or filter.
2. **Given** an archived project, **when** its workspace opens, **then** existing phases,
   attributed emissions, linked parcels, removals, restorations, and report history remain
   visible according to the user's permissions.
3. **Given** an archived project, **when** a user attempts to start or submit a new
   project-context emission or nature intervention, **then** the operation is blocked.
4. **Given** an archived project, **when** a user attempts to change a project/phase or
   project/parcel relationship from its workspace, **then** the operation is blocked.
5. **Given** an archived project has emissions in an inventory, **when** it is archived,
   **then** the emissions and their inventory membership remain unchanged.
6. **Given** an archived project shares a parcel or restoration with another project,
   **when** it is archived, **then** the shared canonical record and the other project's
   relationship remain unchanged.
7. **Given** a correction to an archived project's canonical evidence is legally or
   operationally required, **when** a user follows the applicable global inventory or land
   correction workflow, **then** the existing permissions, verification locks, and audit
   controls still apply independently of project archive state.

The archive contract is intentionally narrower than a full project lifecycle. The status
representation and any future transition model require implementation review, but archive
must never be implemented as hard deletion or relationship cleanup.

# Proposed BPMN 02 — Project-Centric User Flows

> **Design state: Proposed — not implemented.** These flows are a design gate, not a
> description of current application behaviour.

**Decision:** [ADR 0001](../../decisions/0001-project-centric-workspace.md)  
**Target domain model:** [Proposed UML 01](01-project-centric-workspace-uml.md)  
**Acceptance contracts:** [SDO-PRJ-01…08](../../stories/08-project-workspace.md)

The Mermaid flowcharts use subgraphs as lightweight swimlanes. They deliberately keep
project attribution, inventory membership, and location as separate axes. A project
workspace composes existing canonical records; it does not create a second project-owned
copy of them.

<a id="project-workspace-and-capture"></a>

## 1. Project workspace and project-originated capture

```mermaid
flowchart LR
    subgraph Project_manager
        direction TB
        PW1["Open a project workspace"]
        PW2{"View data or create an emission?"}
    end

    subgraph Project_workspace
        direction TB
        PW3["Send the explicit ProjectId"]
        PW4{"Is the project archived?"}
        PW5["Show the workspace as read-only"]
        PW6["Fix ProjectId to the open project"]
        PW7["Optionally select a phase from that project"]
        PW8["Optionally select an inventory independently"]
        PW9["Refresh the project view from canonical records"]
    end

    subgraph Domain_services
        direction TB
        PW10["Validate permission and same-entity ownership"]
        PW11["Query canonical records through explicit project relationships"]
        PW12["Validate phase belongs to project and inventory belongs to entity"]
        PW13["Calculate and save one canonical EmissionsData record"]
        PW14["Leave unrelated and unassigned corporate emissions in global views"]
    end

    PW1 --> PW3 --> PW10 --> PW4
    PW4 -->|Yes| PW5 --> PW11 --> PW9
    PW4 -->|No| PW2
    PW2 -->|View| PW11
    PW2 -->|Create emission| PW6 --> PW7 --> PW8 --> PW12 --> PW13 --> PW9
    PW11 --> PW14
```

`ProjectId` is fixed only because this capture began inside the project workspace. The
optional `InventoryId` still controls formal inventory membership; the workspace cannot
assign it implicitly. Emissions created globally without a project remain valid and do not
appear in this project view.

<a id="global-and-inventory-capture"></a>

## 2. Global and inventory-originated emissions capture

```mermaid
flowchart LR
    subgraph Sustainability_manager
        direction TB
        GI1["Start emissions capture"]
        GI2{"Started inside an inventory?"}
    end

    subgraph Capture_form
        direction TB
        GI3["Global route: InventoryId optional"]
        GI4["Inventory route: fix the selected InventoryId"]
        GI5["Choose an optional ProjectId independently"]
        GI6{"Was a project selected?"}
        GI7["Optionally choose a phase from that project"]
        GI8["Continue with no project"]
    end

    subgraph Domain_service
        direction TB
        GI9["Validate every supplied identifier against the same entity"]
        GI10["Calculate and save one canonical emissions record"]
        GI11{"Does the record have an InventoryId?"}
        GI12["Include it as an exact inventory member"]
        GI13["Keep it outside formal inventory totals"]
    end

    subgraph Assurance_process
        direction TB
        GI14["Verify and lock the exact inventory membership"]
        GI15["Treat project only as attribution and filtering"]
    end

    GI1 --> GI2
    GI2 -->|No| GI3 --> GI5
    GI2 -->|Yes| GI4 --> GI5
    GI5 --> GI6
    GI6 -->|Yes| GI7 --> GI9
    GI6 -->|No| GI8 --> GI9
    GI9 --> GI10 --> GI11
    GI11 -->|Yes| GI12 --> GI14 --> GI15
    GI11 -->|No| GI13
```

The absence of `ProjectId` is not a validation error. Inventory and project are orthogonal:
an inventory may contain records from several projects and ordinary operations, while a
project may have records inside and outside a particular inventory.

<a id="parcel-and-nature-intervention"></a>

## 3. Parcel and nature-intervention capture

```mermaid
flowchart LR
    subgraph Nature_user
        direction TB
        PN1["Start from a project workspace or the global land view"]
        PN2{"Project workspace?"}
        PN3["Use the open ProjectId"]
        PN4["ProjectId remains optional"]
        PN5["Select the exact entity-owned parcel"]
        PN6{"Tree removal or restoration?"}
        PN7["Enter species and removal source measurements"]
        PN8["Enter species, area, dates and restoration source inputs"]
    end

    subgraph Nature_service
        direction TB
        PN9["Validate entity, project and parcel relationships"]
        PN10["Link parcel to project when applicable without changing parcel ownership"]
        PN11["Calculate derived carbon values on the server"]
        PN12["Preserve source inputs and store calculated outputs separately"]
        PN13["Save one canonical event with parcel and project relationships"]
        PN14{"Is the saved event a restoration shared by several projects?"}
        PN15["Flag it as shared and unallocated for reporting"]
        PN18["Complete the canonical event"]
    end

    subgraph Deferred_observation_model
        direction TB
        PN16["Deferred: dated ecosystem occurrence, baseline, condition and evidence"]
        PN17["Do not present this schema as implemented in the first slice"]
    end

    PN1 --> PN2
    PN2 -->|Yes| PN3 --> PN5
    PN2 -->|No| PN4 --> PN5
    PN5 --> PN9 --> PN10 --> PN6
    PN6 -->|Tree removal| PN7 --> PN11
    PN6 -->|Restoration| PN8 --> PN11
    PN11 --> PN12 --> PN13 --> PN14
    PN14 -->|Yes| PN15 --> PN18
    PN14 -->|No| PN18
    PN16 --> PN17
```

A parcel is required for these nature events because it is the durable spatial boundary.
The project link supplies operational context and can coexist with other project links; it
does not transfer or duplicate the parcel. The disconnected deferred lane is intentional:
dated ecosystem observations and baselines require a separate approved schema.

<a id="project-reporting"></a>

## 4. Project reporting with explicit accounting boundaries

```mermaid
flowchart LR
    subgraph Report_requester
        direction TB
        PR1["Select one ProjectId"]
        PR2["Choose a date range or one inventory whose dates become the range"]
        PR3["Submit explicit report parameters"]
    end

    subgraph Report_orchestrator
        direction TB
        PR4["Validate tenant, permission and complete boundary parameters"]
        PR5["Read only records explicitly attributed to the project"]
        PR6{"Is a restoration linked to several projects?"}
        PR7["List it as shared and omit it from additive project totals until allocated"]
        PR8["Keep all accounting categories separate"]
    end

    subgraph Canonical_domain_reads
        direction TB
        PR9["Operational emissions as period flows"]
        PR10["Biomass stock loss as dated nature impacts"]
        PR11["Restoration sequestration as labelled estimates as of the range end"]
        PR12["Supported credit or retirement evidence as a separate claim section"]
    end

    subgraph Report_output
        direction TB
        PR13["Show units, methods, time basis, inclusions and exclusions"]
        PR14["State the selected dates and derived nature as-of date"]
        PR15["State that a project report is not inventory verification"]
        PR16["Never calculate an automatic net project carbon figure"]
    end

    PR1 --> PR2 --> PR3 --> PR4 --> PR5
    PR5 --> PR9 --> PR8
    PR5 --> PR10 --> PR8
    PR5 --> PR11 --> PR6
    PR6 -->|Yes| PR7 --> PR8
    PR6 -->|No| PR8
    PR5 --> PR12 --> PR8
    PR8 --> PR13 --> PR14 --> PR15 --> PR16
```

The first slice may show existing offset or retirement evidence, but it must not infer a
verified retirement or a credit ledger that does not exist. Gross operational emissions,
biomass loss, restoration estimates, and credit claims have different units, time bases, and
assurance status; they are reported alongside one another and never silently netted.

<a id="archive-and-history"></a>

## 5. Project archive and historical continuity

```mermaid
flowchart LR
    subgraph Project_owner
        direction TB
        AH1["Request project archive"]
        AH2["Review the effect on new project-context work"]
        AH3["Confirm archive"]
        AH4["Open an archived project"]
        AH5["Attempt new project-originated capture"]
    end

    subgraph Lifecycle_service
        direction TB
        AH6["Validate permission and same-entity ownership"]
        AH7["Persist an explicit archived state"]
        AH8["Block new project and phase mutations"]
        AH9["Reject new capture in the archived project context"]
        AH10["Never hard-delete as a substitute for archive"]
    end

    subgraph Canonical_domains
        direction TB
        AH11["Preserve emissions and inventory membership"]
        AH12["Preserve parcel ownership and reuse"]
        AH13["Preserve nature events, evidence and relationships"]
        AH14["Keep global capture available without a project"]
    end

    subgraph Historical_readers
        direction TB
        AH15["Show the archived workspace as read-only"]
        AH16["Keep reports and audit history accessible with an archived label"]
    end

    AH1 --> AH2 --> AH3 --> AH6 --> AH7 --> AH8 --> AH10
    AH7 --> AH11
    AH7 --> AH12
    AH7 --> AH13
    AH4 --> AH6 --> AH15 --> AH16
    AH5 --> AH9 --> AH14
```

Archive is a lifecycle state, not cascading deletion. If the current model cannot represent
that state reliably, the archive mutation needs a separate schema decision; the product must
not simulate archive by deleting the project or severing its canonical relationships.

## Exception and guardrail matrix

| Flow | Condition | Required outcome |
|---|---|---|
| Workspace or report | Project is missing, inaccessible, or belongs to another entity | Return not found; do not reveal cross-tenant existence or related counts. |
| Project capture | Project is archived | Render existing data read-only and reject new project-context writes. |
| Emissions capture | Phase does not belong to selected project | Reject before calculation or persistence. |
| Emissions capture | Inventory belongs to another entity or is locked | Reject the assignment; preserve existing inventory verification rules. |
| Global capture | No project selected | Accept it as valid corporate activity data. |
| Nature capture | No exact parcel selected | Reject the event; never use the project itself as a spatial substitute. |
| Nature capture | Parcel belongs to another entity | Reject it even if a supplied project identifier is valid. |
| Project report | Neither a complete date range nor an inventory is supplied | Reject the request before creating a report job; never default a formal report silently to all time. |
| Project report | Restoration is attributed to more than one project | Show it as shared and unallocated; exclude it from additive project totals until an approved allocation method exists. |
| Project report | Offset exists without reliable retirement evidence | Label only what the evidence supports; do not call it a retired credit. |
| Any flow | Project relation is absent from an otherwise valid global record | Do not place it in a generic error queue or invent a synthetic project. |

## First-slice and deferred boundary

| First slice using existing relationships | Deliberately deferred pending a separate design decision |
|---|---|
| Derived project workspace over canonical records | Operational site, facility, source, meter or asset schema |
| Project-context preselection with entity and phase validation | Dated ecosystem occurrence, baseline, condition and observation history |
| Global and inventory capture with optional project attribution | Counterfactual project-impact accounting and avoided-emissions claims |
| Parcel-first removal and restoration capture with zero or one project selected for a new event | Multi-project amount or percentage allocation engine |
| Explicitly bounded project reports with separated categories | Credit-lot, holding and retirement ledger |
| Read-only archive contract without deletion | Scoped project, inventory and entity targets |

The archive contract belongs in acceptance tests before release. If a reliable archived state
cannot be represented without a migration, that mutation moves to the deferred column while
read-only historical continuity remains a non-negotiable constraint on the eventual design.

---

*Current process references: [Emissions lifecycle](../bpmn/02-emissions-lifecycle.md),
[Inventory verification](../bpmn/03-inventory-verification.md),
[Report generation](../bpmn/05-report-generation.md), and
[Nature tracking](../bpmn/06-nature-tracking.md).*

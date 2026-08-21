# 05 · Reporting & Notifications

Asynchronous report generation and the in-app notification inbox. This is the only
user-triggered async process in the platform — everything else on the request path is
synchronous.

Conventions, statuses and the story template are defined in [README.md](README.md).

---

<a id="sdo-rep-01"></a>

### SDO-REP-01 · Queue a report

**As a** sustainability manager
**I want** to request a report by type and format
**so that** I can take an audit-ready document to a board or an assurance provider.

| | |
|---|---|
| **Status** | ✅ Built |
| **Role** | Any authenticated member of the entity |
| **Diagram** | [BPMN 05 — report generation](../diagrams/bpmn/05-report-generation.md) |
| **Code** | `backend/apps/reports/views.py` · `ReportJobsViewSet` |
| **Tests** | `backend/apps/reports/tests/test_feature_gate.py` |
| **Linear** | `area:rep` · `type:spec` |

Four types: `emissions_summary`, `ghg_inventory`, `phase_progress`, `tree_log`.
Three formats: `pdf`, `csv`, `json`.

**Acceptance criteria**

1. **Given** a valid type and format, **when** the user POSTs to `/api/reports/`,
   **then** a `ReportJobs` row is created with `JobStatus = 1` (Queued) and `RequestedBy` set
   to the caller.
2. **Given** the request, **when** it is accepted, **then** `EntityId` comes from
   `request.entity_id` and is never read from the request body.
3. **Given** a type outside the four choices, **when** submitted, **then** the response is 400.

<a id="sdo-rep-02"></a>

### SDO-REP-02 · The request returns immediately; generation happens in the background

**As a** user requesting a large report
**I want** the request to return at once
**so that** the browser is not held open while a PDF renders.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 06 §6.4](../diagrams/uml/06-sequences.md) · [UML 08 — queue routing](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/apps/reports/views.py` · `_queue_report()` → `tasks.reports.generate_report` |
| **Tests** | `backend/tasks/tests/test_reports.py` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** a queued job, **when** the response is returned, **then** it carries the
   `ReportJobId` and the HTTP request does not wait for rendering.
2. **Given** the task name prefix `tasks.reports.*`, **when** it is dispatched, **then** it is
   routed to the `reports` queue, not `default`.
3. **Given** the reports worker, **when** it runs, **then** it recycles after 10 tasks
   (`--max-tasks-per-child=10`), because PDF rendering accumulates memory.

<a id="sdo-rep-03"></a>

### SDO-REP-03 · Job status is observable through four states

**As a** user waiting on a report
**I want** to see where my job has got to
**so that** I know whether to wait or retry.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 07 §7.3 — report job states](../diagrams/uml/07-state-machines.md) |
| **Code** | `backend/apps/reports/models.py` · `REPORT_STATUS_CHOICES` |
| **Tests** | `backend/tasks/tests/test_reports.py` |
| **Linear** | `area:rep` · `type:spec` |

States: 1 Queued → 2 Processing → 3 Complete, or → 4 Failed.

**Acceptance criteria**

1. **Given** the worker picks up the task, **when** it starts, **then** `JobStatus = 2` and
   `StartedAt` is set.
2. **Given** rendering succeeds, **when** the object is stored, **then** `JobStatus = 3` with
   `S3Key`, `FileSizeBytes` and `CompletedAt` populated.
3. **Given** rendering raises, **when** the failure is handled, **then** `JobStatus = 4` and
   `ErrorMessage` holds the first 500 characters of the exception.

<a id="sdo-rep-04"></a>

### SDO-REP-04 · A completed report is downloaded through a pre-signed URL

**As a** user
**I want** to download my finished report
**so that** I can circulate it.

| | |
|---|---|
| **Status** | 🟡 Partial — the status guard is implemented; no test exercises a successful download |
| **Diagram** | [BPMN 05](../diagrams/bpmn/05-report-generation.md) |
| **Code** | `backend/apps/reports/views.py` · `download()` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** a job with `JobStatus = 3`, **when** the user GETs `/api/reports/{id}/download/`,
   **then** a pre-signed URL is returned, expiring per `AWS_S3_PRESIGNED_URL_EXPIRY`.
2. **Given** a job in any other status, **when** download is attempted, **then** it is refused.
3. **Given** a job belonging to another entity, **when** download is attempted, **then** it is
   not found — tenant scoping applies to reports like everything else.

<a id="sdo-rep-05"></a>

### SDO-REP-05 · The user is told when a report is ready

**As a** user who queued a report
**I want** to be notified on completion
**so that** I need not poll.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 06 §6.4](../diagrams/uml/06-sequences.md) |
| **Code** | `backend/tasks/reports.py` · `_notify_complete()` |
| **Tests** | `backend/tasks/tests/test_reports.py` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** a job reaching `JobStatus = 3`, **when** it completes, **then** a notification of
   type `report_ready` is created for `RequestedBy`.

<a id="sdo-rep-06"></a>

### SDO-REP-06 · A failure is only announced once no retries remain

**As a** user
**I want** not to be told my report failed when a retry is about to succeed
**so that** I do not re-request work already in flight.

| | |
|---|---|
| **Status** | ✅ Built — changed by [F4](../diagrams/FINDINGS.md#f4) |
| **Diagram** | [BPMN 05 — failure ordering](../diagrams/bpmn/05-report-generation.md) |
| **Code** | `backend/tasks/reports.py` |
| **Tests** | `backend/tasks/tests/test_reports.py` |
| **Linear** | `area:rep` · `type:spec` |

`generate_report` retries twice with a 60-second delay, under a 300-second hard time limit.

**Acceptance criteria**

1. **Given** an attempt fails with retries remaining, **when** the failure is handled,
   **then** `JobStatus` becomes 4 but **no** `report_failed` notification is sent.
2. **Given** the final attempt fails, **when** `self.request.retries >= self.max_retries`,
   **then** exactly one `report_failed` notification is sent.
3. **Given** a job that fails once then succeeds, **when** the user checks their inbox,
   **then** they see only `report_ready`.

<a id="sdo-rep-07"></a>

### SDO-REP-07 · Expired reports and their stored files are purged

**As a** data protection owner
**I want** generated reports to age out
**so that** exported personal and commercial data does not accumulate indefinitely.

| | |
|---|---|
| **Status** | 🟡 Partial — implemented; no test covers the purge |
| **Diagram** | [UML 08 — beat schedule](../diagrams/uml/08-async-topology.md) |
| **Code** | `backend/tasks/reports.py` · `purge_expired_reports()`, `_delete_s3_objects()` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** jobs past their retention window, **when** the 04:00 task runs, **then** both the
   `ReportJobs` rows and their stored objects are deleted.
2. **Given** object deletion fails, **when** the task runs, **then** the failure is logged
   rather than silently leaving an orphaned row.

<a id="sdo-rep-08"></a>

### SDO-REP-08 · Export format is gated by the entity's plan

**As a** platform owner
**I want** CSV and JSON export to be a paid capability
**so that** the pricing tiers mean something.

| | |
|---|---|
| **Status** | ✅ Built |
| **Diagram** | [UML 05 — gate enforcement](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/reports/views.py` · `_require_export_feature()` |
| **Tests** | `backend/apps/reports/tests/test_feature_gate.py` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** an entity whose plan lacks the export feature, **when** it requests a CSV or JSON
   report, **then** the response is 402 with `code = "feature_gated"`.
2. **Given** a SuperAdmin, **when** they request the same, **then** the gate is bypassed.

<a id="sdo-rep-09"></a>

### SDO-REP-09 · An in-app inbox shows what needs attention

**As a** user
**I want** notifications in the product
**so that** verification, unlock and report events reach me without email.

| | |
|---|---|
| **Status** | 🟡 Partial — implemented; `backend/apps/notifications/` has no test package |
| **Diagram** | [UML 05 — notifications](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/notifications/views.py` · `NotificationsViewSet` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** an authenticated user, **when** they list `/api/notifications/`, **then** they see
   only their own, scoped to the active entity.
2. **Given** one notification, **when** they PATCH it, **then** `IsRead` is set with `ReadAt`.
3. **Given** several unread, **when** they POST to `/api/notifications/read-all/`, **then** all
   of theirs in that entity are marked read.

<a id="sdo-rep-10"></a>

### SDO-REP-10 · Ten event types raise a notification

**As a** user
**I want** the events that matter to notify me
**so that** I do not have to watch for state changes.

| | |
|---|---|
| **Status** | 🟡 Partial — the vocabulary is declared; only some types are actually raised |
| **Diagram** | [UML 05](../diagrams/uml/05-domain-platform.md) |
| **Code** | `backend/apps/notifications/models.py` · `NOTIFICATION_TYPE_CHOICES` |
| **Linear** | `area:rep` · `type:spec` |

Declared types: `user_created`, `emissions_submitted`, `emissions_verified`,
`emissions_unlocked`, `system_error`, `access_denied`, `entity_created`, `password_reset`,
`report_ready`, `report_failed`.

**Acceptance criteria**

1. **Given** each declared type, **when** the codebase is searched for a `notify()` call
   raising it, **then** either a producer exists or the type is removed from the vocabulary.
2. **Given** a notification, **when** created, **then** `RelatedModule` and `RelatedRecordId`
   point at the record it concerns, so the UI can deep-link.

> Verified producers today include `emissions_verified`, `emissions_unlocked`, `report_ready`
> and `report_failed`. The remaining types are declared but not confirmed to be raised
> anywhere — worth an audit before the UI promises them.

<a id="sdo-rep-11"></a>

### SDO-REP-11 · Reports are written to object storage under a tenant-scoped key

**As a** platform operator
**I want** every generated file addressed by node and entity
**so that** storage stays partitioned per tenant.

| | |
|---|---|
| **Status** | 🟡 Partial — see [SDO-GAP-08](07-backlog-gaps.md#sdo-gap-08) |
| **Diagram** | [UML 01 — data tier](../diagrams/uml/01-component-architecture.md) |
| **Code** | `backend/tasks/reports.py` · `_render_report()`, `_upload_to_storage()` |
| **Linear** | `area:rep` · `type:spec` |

**Acceptance criteria**

1. **Given** a completed render, **when** it is stored, **then** the key follows
   `{node_id}/{entity_id}/reports/{uuid}.{fmt}`.
2. **Given** development settings with S3 disabled, **when** a report completes, **then** the
   file is written to `/tmp` inside the container rather than to MinIO — the behaviour
   `SDO-GAP-08` proposes changing.

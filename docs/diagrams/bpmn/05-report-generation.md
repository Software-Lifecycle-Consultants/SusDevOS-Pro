# BPMN 05 — Report Generation & Delivery

The only user-triggered asynchronous process in the platform. Everything else in the
request path is synchronous.


**Related user stories** — [Reporting & notifications — SDO-REP-01…08](../../stories/05-reporting-notifications.md)

## Process

```mermaid
flowchart TB
    subgraph L1["👤 User"]
        A([Needs a report]) --> B[Open /reports]
        B --> C[Choose type:<br/>emissions_summary · ghg_inventory<br/>phase_progress · tree_log]
        C --> D[Choose format:<br/>PDF · CSV · JSON]
        D --> E[POST /api/reports/]
    end

    subgraph L2["⚙️ Django API — synchronous"]
        E --> F{"_require_export_feature(fmt)<br/>plan allows this format?"}
        F -->|"No"| G([402 feature_gated])
        F -->|"Yes"| H[("INSERT ReportJobs<br/>JobStatus = 1 Queued<br/>EntityId, RequestedBy")]
        H --> I[/"_queue_report(job)<br/>generate_report.delay(id)"/]
        I --> J([201 with ReportJobId<br/>returns immediately])
    end

    subgraph L3["📮 Redis — reports queue"]
        I -.-> K[(Task enqueued)]
    end

    subgraph L4["⚙️ celery_reports worker"]
        K --> L[("JobStatus = 2 Processing<br/>StartedAt = now()")]
        L --> M[/"build_report_data(job)"/]
        M --> N[/"Query tenant-scoped rows<br/>for the report type"/]
        N --> O[/"render(data, format)"/]
        O --> P{"Render<br/>succeeded?"}
    end

    subgraph L5["🗄️ S3 / MinIO"]
        P -->|"Yes"| Q[/"PUT node-id/entity-id/<br/>reports/uuid.fmt"/]
    end

    subgraph L6["⚙️ Completion"]
        Q --> R[("JobStatus = 3 Complete<br/>S3Key, FileSizeBytes, CompletedAt")]
        R --> S[("Notification: report_ready")]
        P -->|"No — exception"| T[("JobStatus = 4 Failed<br/>ErrorMessage, 500 chars")]
        T --> U[("✅ F4 — Notification: report_failed<br/>sent only on terminal attempt")]
        U --> V{"Retries<br/>remaining?"}
        V -->|"Yes — max 2, 60s delay"| K
        V -->|"No"| W([Terminal failure])
    end

    subgraph L7["👤 User"]
        S -.-> X[Sees notification]
        X --> Y[GET /reports/id/download/]
        Y --> Z{"JobStatus == 3?"}
        Z -->|"No"| AA([Rejected])
        Z -->|"Yes"| AB[/"Pre-signed S3 URL<br/>expiry from env"/]
        AB --> AC([📄 File downloaded])
        U -.-> AD[Sees failure + reason]
    end

    style G fill:#ffebee,stroke:#b71c1c,color:#000
    style T fill:#ffebee,stroke:#b71c1c,color:#000
    style W fill:#ffebee,stroke:#b71c1c,color:#000
    style AC fill:#e8f5e9,stroke:#1b5e20,color:#000
    style J fill:#e3f2fd,stroke:#0d47a1,color:#000
```

## Timing and resource constraints

| Constraint | Value | Reason |
|------------|-------|--------|
| `time_limit` | 300s | Hard kill — a runaway PDF render must not occupy a worker |
| `max_retries` | 2 | Transient S3/DB faults recover; deterministic render bugs do not |
| `default_retry_delay` | 60s | Space out retries against a recovering dependency |
| `--max-tasks-per-child` | 10 | Recycle workers — PDF rendering accumulates memory |
| Worker concurrency | 2 | Reports are memory-heavy; a narrow queue protects the box |

## Retention

```mermaid
flowchart LR
    A([Report completes]) --> B[(S3 object +<br/>ReportJobs row)]
    B --> C{"Past retention<br/>window?"}
    C -->|"No"| D([Downloadable])
    C -->|"Yes"| E[/"purge_expired_reports<br/>04:00 daily"/]
    E --> F[/"_delete_s3_objects(keys)"/]
    F --> G([Object + row removed])

    style E fill:#fff3e0,stroke:#e65100,color:#000
```

## ✅ F4 · Failure notification ordering — fixed

> The worker used to mark the job `Failed` **and send `report_failed`** before calling
> `self.retry()` (`backend/tasks/reports.py:65-68`) — so a job that succeeded on its second
> attempt had already told the user it failed, then later told them it was ready, and they
> could re-request a report that was already in flight.
> **Now:** `_notify_failed()` fires only once `self.request.retries >= self.max_retries`,
> deferring the notification to the terminal attempt. The `JobStatus = 4` write still happens
> on every attempt — "Failed" is an honest description of the job's state between attempts; it
> was only the *notification* that was premature. Three tests cover retries-remaining, the
> terminal attempt, and the happy path.
> See [F4 in the findings register](../FINDINGS.md#f4).

```mermaid
flowchart LR
    A([Attempt 1 raises]) --> B[JobStatus = 4 Failed]
    B --> C{"Retries<br/>remaining?"}
    C -->|"Yes - no notification"| D[self.retry]
    D --> E([Attempt 2 succeeds])
    E --> F[JobStatus = 3 Complete]
    F --> G[/"Notify: report_ready"/]
    G --> H([User receives ONE<br/>accurate notification])
    C -->|"No - terminal attempt"| I[/"Notify: report_failed"/]
    I --> J([User notified only<br/>on the final failure])

    style H fill:#e8f5e9,stroke:#1b5e20,color:#000
    style J fill:#fff3e0,stroke:#e65100,color:#000
```

## Local development note

`_upload_to_storage()` branches on settings: S3/MinIO in normal operation, a `/tmp` write in
development. A report generated in a local container therefore lands inside that container's
filesystem, not in MinIO, unless S3 storage is enabled in the environment.

---
*Source: `backend/tasks/reports.py`, `backend/apps/reports/views.py`,
`backend/apps/reports/models.py`, `backend/apps/reports/renderers.py`,
`backend/config/celery.py`*

# 06 — Request & Calculation Sequences

The four interaction paths a reviewer most needs to trace end to end.

## 6.1 Login, tenant resolution, and refresh

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant FE as Next.js frontend
    participant MW as TenantQueryMiddleware
    participant DRF as DRF dispatch
    participant AU as RevokedTokenJWTAuthentication
    participant V as View
    participant DB as PostgreSQL

    U->>FE: submit username + password
    FE->>MW: POST /api/auth/login
    Note over MW: user is AnonymousUser<br/>entity_id = None
    MW->>DRF: pass through
    DRF->>V: LoginView (AllowAny)
    V->>DB: authenticate credentials
    DB-->>V: Users row
    V->>V: issue_tokens(user)
    V->>V: set_refresh_cookie(response)
    V-->>FE: 200 access_token + user + entity_id + role<br/>Set-Cookie refresh_token HttpOnly<br/>Path=/api/auth/refresh Max-Age=604800
    FE->>FE: access token to Zustand (memory only)

    rect rgba(120,160,255,0.10)
        Note over FE,DB: Subsequent authenticated request
        FE->>MW: GET /api/emissions/<br/>Authorization Bearer + X-Entity-ID
        MW->>MW: request.user not authenticated yet
        MW->>MW: request.entity_id = None
        MW->>DRF: continue
        DRF->>AU: authenticate()
        AU->>DB: is Jti in RevokedTokens?
        DB-->>AU: not revoked
        AU-->>DRF: (user, token)
        DRF->>V: initial() runs perms
        V->>V: EntityScopeInitialMixin<br/>resolve_request_entity_id()
        Note over V: SuperAdmin - any X-Entity-ID<br/>others - must belong via<br/>EntityMembers or home entity
        V->>DB: get_queryset().filter(EntityId=entity_id, Status__lt=4)
        DB-->>V: tenant-scoped rows
        V-->>FE: 200 results
    end

    rect rgba(255,180,120,0.12)
        Note over FE,DB: Access token expires after 15 min
        FE->>V: POST /api/auth/refresh (cookie only)
        V->>DB: validate refresh, check RevokedTokens
        V-->>FE: 200 new access_token
    end

    U->>FE: logout
    FE->>V: POST /api/auth/logout
    V->>DB: INSERT RevokedTokens(Jti, ExpiresAt)
    V->>V: clear_refresh_cookie()
    V-->>FE: 205 / 200
```

Revocation is server-side and immediate: `RevokedTokenJWTAuthentication.get_validated_token()`
rejects any token whose `Jti` is present in `RevokedTokens`, rather than waiting for the
15-minute expiry. `tasks.auth.purge_expired_revoked_tokens` (05:00 daily) sweeps rows whose
underlying token has expired anyway.

## 6.2 Emissions record creation and server-side calculation

```mermaid
sequenceDiagram
    autonumber
    actor U as Contributor
    participant V as EmissionsDataViewSet
    participant M as EmissionsData.save()
    participant S as emissions.services
    participant DB as PostgreSQL

    U->>V: POST /api/emissions/ with QuantityOrCost,<br/>InputUnitId, EmissionFactor, Scope,<br/>and (ignored) EmissionsAmount
    V->>V: FeatureGateMixin - required_feature
    V->>V: TenantViewSetMixin.perform_create()<br/>EntityId = request.entity_id<br/>CreatedBy = request.user.UserId
    Note over V: EntityId from request body is never trusted
    V->>M: save()
    M->>S: compute_emissions(instance)

    alt QuantityOrCost or EmissionFactor is None
        S-->>M: return - nothing to compute
    else inputs present
        S->>S: _apply_unit_conversion()
        Note over S: QuantityCanonical =<br/>QuantityOrCost x Unit.ConversionFactor<br/>(falls back to raw when no factor)
        S->>S: _compute_amounts()
        S->>DB: _get_gwp_factor() - GwpValues lookup
        DB-->>S: GWP100 for gas/subtype
        Note over S: kg CO2e = qty x EF x GWP100<br/>EmissionsAmount = kg<br/>EmissionsAmountTonnes = kg / 1000

        opt BiogenicCO2FactorKg is not None
            S->>S: BiogenicCO2AmountTonnes = qty x factor / 1000
            Note over S: EXCLUDED from EmissionsAmount<br/>(GHG Protocol, critical rule 4)
        end

        opt Scope == 2
            S->>S: _compute_scope2()
            Note over S: LocationBased = qty x EFLocationBased<br/>MarketBased = qty x EFMarketBased<br/>each falls back to the generic result<br/>primary = market-based when available
        end
    end

    S-->>M: instance mutated in place
    M->>DB: INSERT with server-computed fields
    DB-->>V: saved row
    V->>V: _audit("Create", instance)
    V-->>U: 201 with authoritative amounts
```

Three behaviours worth confirming in review, all deliberate and commented in
`services.py`:

- `QuantityCanonical` is tested with `is None`, not truthiness — a legitimate canonical
  value of zero must not silently revert to the raw quantity.
- Clearing `BiogenicCO2FactorKg` on a re-save also clears `BiogenicCO2AmountTonnes`,
  so a record that stops being biogenic does not keep reporting a stale figure.
- Scope 2 location/market amounts are recomputed unconditionally on every save (`else`,
  not `elif ... is None`), which keeps re-saves idempotent instead of retaining a stale
  value from the previous save.

## 6.3 Verification and unlock

```mermaid
sequenceDiagram
    autonumber
    actor VER as Verifier
    actor SA as SuperAdmin
    participant V as EmissionsDataViewSet
    participant S as emissions.services
    participant N as notifications.services
    participant DB as PostgreSQL

    VER->>V: POST /api/emissions/{id}/verify/
    V->>V: permission check
    Note over V: verify_record() now guards itself -<br/>raises on double-verification (F3, fixed)
    V->>S: verify_record(instance, verified_by, notes)
    S->>DB: VerificationStatus = 3<br/>VerifiedBy, VerifiedAt, VerificationNotes
    S->>N: notify(CreatedBy, "emissions_verified")
    N->>DB: INSERT Notifications
    S-->>V: done
    V-->>VER: 200 - record now locked

    rect rgba(255,140,140,0.12)
        Note over SA,DB: Later - the record must be corrected
        SA->>V: POST /api/emissions/{id}/unlock/ with reason
        V->>V: SuperAdmin guard now enforced in BOTH<br/>the view and unlock_record() (F9, fixed)
        V->>S: unlock_record(instance, reason, unlocked_by, entity_id)
        S->>DB: VerificationStatus = 1
        S->>DB: INSERT AuditLog<br/>Action=Unlock_Verified, RetentionTier=3 (7 years)
        S->>N: notify(CreatedBy, "emissions_unlocked")
        S-->>V: done
        V-->>SA: 200 - editable again
    end
```

The unlock path is the compliance-sensitive one: it is SuperAdmin-only, requires a reason,
and always writes a 7-year-retention audit row.

> **✅ F9 · Authorization — guard moved into the service — fixed 2026-08-21.**
> `unlock_record()` (`apps/emissions/services.py:169`) performed the privileged state change
> and wrote the mandatory audit row, but its own docstring said outright: *"Only callable by
> SuperAdmin — the view enforces that guard."* The function itself checked nothing, so any
> future call site that was not the viewset — a management command, an admin action, a
> bulk-correction task — could unlock verified records with no SuperAdmin check.
> **Now:** `unlock_record()` raises `PermissionDenied` when `unlocked_by` is not a SuperAdmin —
> it already received the acting user, so it always had the context to check. The guard runs
> before any mutation or audit write, so a rejected unlock leaves no trace. The view's inline
> check is retained for its specific response body, so the guard now lives in both places. This
> was the same structural pattern as **F3**, fixed the same way: the check now sits in the
> layer that owns the invariant.
> See [F9 in the findings register](../FINDINGS.md#f9).

## 6.4 Asynchronous report generation

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant V as ReportJobsViewSet
    participant DB as PostgreSQL
    participant R as Redis (reports queue)
    participant W as celery_reports worker
    participant REN as reports.renderers
    participant S3 as S3 / MinIO
    participant N as Notifications

    U->>V: POST /api/reports/ - type, format
    V->>V: _require_export_feature(fmt)
    V->>DB: INSERT ReportJobs JobStatus=1 Queued
    V->>V: _queue_report(job)
    V->>R: generate_report.delay(job.ReportJobId)
    V-->>U: 201 with ReportJobId - returns immediately

    R->>W: deliver task
    W->>DB: JobStatus=2 Processing, StartedAt=now()
    W->>REN: build_report_data(job)
    REN->>DB: gather rows for the report type
    DB-->>REN: dataset
    REN->>REN: render(data, job.Format)
    REN-->>W: bytes
    W->>S3: PUT node-id/entity-id/reports/uuid.fmt
    S3-->>W: stored

    alt success
        W->>DB: JobStatus=3 Complete, S3Key, FileSizeBytes, CompletedAt
        W->>N: _notify_complete(job) - report_ready
    else exception
        W->>DB: JobStatus=4 Failed, ErrorMessage (500 chars), CompletedAt
        W->>N: _notify_failed() now fires only on<br/>the terminal attempt (F4, fixed)
        W->>R: self.retry() - max_retries=2, 60s delay
    end

    U->>V: GET /api/reports/{id}/download/
    V->>V: reject unless JobStatus == 3
    V->>S3: presigned URL
    V-->>U: 302 / URL
```

`generate_report` carries `time_limit=300`, `max_retries=2`, `default_retry_delay=60`. The
worker runs with `--max-tasks-per-child=10` because PDF rendering leaks memory over time.

> **✅ F4 · UX / async — notification deferred to the terminal attempt — fixed 2026-08-21.**
> In `backend/tasks/reports.py:65-68` the job used to be marked `Failed` and `_notify_failed()`
> fired, and only then was `self.retry()` raised — so a transient S3 timeout on attempt 1 told
> the user their report failed, and a successful attempt 2 sixty seconds later told them it was
> ready. The user got a failure notice for a report that worked, and could re-request one
> already being generated.
> **Now:** `_notify_failed()` fires only when `self.request.retries >= self.max_retries`. The
> `JobStatus = 4` write still happens on every attempt — "Failed" is an honest description of
> the job's state between attempts; it was only the *notification* that was premature. Three
> tests cover retries-remaining, the terminal attempt, and the happy path.
> See [F4 in the findings register](../FINDINGS.md#f4).

---
*Source: `backend/apps/users/views.py`, `backend/apps/users/authentication.py`,
`backend/apps/entities/middleware.py`, `backend/apps/shared/views.py`,
`backend/apps/emissions/services.py`, `backend/apps/reports/views.py`,
`backend/tasks/reports.py`*

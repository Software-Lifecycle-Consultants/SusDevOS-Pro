# Review Findings Register

Observations surfaced while deriving the [architecture diagram set](README.md) from source,
tagged `F1`–`F10` so a reviewer can move between this register and the diagrams.

> **Status: all resolved (2026-08-21).** Every finding below has been fixed and verified
> against a running stack — `219 passed`, up from a `199` baseline. Each entry keeps its
> original description as a record of *why* the change was made, followed by a **Resolution**
> note stating what was actually done. Two findings changed shape once investigated, and one
> was rejected on inspection rather than "fixed"; those are called out explicitly.

## Register

| ID | Category | Finding | Resolution |
|----|----------|---------|------------|
| **F1** | Tenant isolation | `Ecosystem` / `Species` scope by convention, not by FK | ✅ Real `ForeignKey` + `TenantViewSetMixin` |
| **F2** | Authorization | Only the first active role is consulted | ✅ Union across all active roles |
| **F3** | Data integrity | `verify_record()` has no double-verification guard | ✅ Guard moved into the service |
| **F4** | UX / async | `report_failed` is sent before the retry is attempted | ✅ Deferred to the terminal attempt |
| **F5** | Doc drift | Feature gate returns **402**, not documented | ✅ `CLAUDE.md` corrected |
| **F6** | Operational | Tasks in `tasks/` need an explicit import to register | ✅ `beat_init` validator + CI test |
| **F7** | Operational | Two tasks absent from `beat_schedule` | ✅ One scheduled, one confirmed intentional |
| **F8** | Billing | `past_due` loses gated features immediately | ✅ Grace until `CurrentPeriodEnd` |
| **F9** | Authorization | Unlock guard lives in the view, not the service | ✅ Guard moved into the service |
| **F10** | Authorization | `verify` was open to any authenticated user *(found during the fix)* | ✅ Restricted to Manager+ |

### What changed once investigated

- **F1 was far cheaper than feared.** Adding `db_column="EntityId"` to the new `ForeignKey`
  keeps the existing column, so the migration is two `AlterField`s that add an FK constraint
  and an index — no rename, no data migration, no table rewrite. Verified with `sqlmigrate`.
- **F2 was less severe than originally written.** `assign_role` already retires the previous
  role before creating a new one, and `IsEntityAdmin`/`IsManagerOrAbove` already scanned all
  active roles. Only `_resolve_privilege` was single-role, so this was a latent inconsistency
  rather than a live bug.
- **F8 had no producer.** Nothing in the repo ever *sets* `past_due` — there is no Stripe
  webhook and no dunning logic. The fix is forward-looking policy, not a live outage.
- **F6's first fix was wrong and the new test caught it.** See F6 below.

---

<a id="f1"></a>

## F1 · Ecosystem and Species scope by convention, not by foreign key

**Category:** Tenant isolation · **Confidence:** High — directly readable in the model

`Ecosystem.EntityId` and `Species.EntityId` are declared as plain `IntegerField`s carrying a
`help_text="FK to entities.Entities"`, rather than as actual `ForeignKey` relations:

```python
EntityId = models.IntegerField(help_text="FK to entities.Entities")
```

Because there is no relation, `TenantViewSetMixin.get_queryset()` — which filters
`.filter(EntityId=entity_id)` on a related field — cannot be used. Those viewsets therefore
mix in only `EntityScopeInitialMixin` and enforce scoping in their own `get_queryset()`.

**Failure scenario.** A new endpoint added to `apps/ecosystem/` that defines its own
`get_queryset()` without an `EntityId` filter returns every tenant's species and ecosystems.
Nothing in the ORM or the mixin prevents it, and no exception is raised — the leak is silent.

**Mitigation already present.** `apps/ecosystem/tests/test_tenant_scope.py` and
`apps/land/tests/test_ecosystem_link_isolation.py` are regression tests for exactly this.

**To confirm:** whether the `IntegerField` choice was deliberate (avoiding a circular app
dependency, perhaps) or historical. If historical, converting to a real `ForeignKey` would
let both apps use `TenantViewSetMixin` and make the isolation structural.

**Resolution (2026-08-21).** Both fields are now real foreign keys:
`models.ForeignKey("entities.Entities", on_delete=models.PROTECT, db_column="EntityId")`,
with `related_name` `ecosystems` and `species_records`. `db_column` keeps the existing column
name, so migration `ecosystem/0004` emits only `CREATE INDEX` + `ADD CONSTRAINT FOREIGN KEY` —
confirmed by reading `sqlmigrate` output before applying, then applied cleanly to the running
database.

Both viewsets now use `TenantViewSetMixin` instead of hand-rolled filtering, so isolation is
structural rather than conventional. That also closed a gap nobody had flagged: these two
viewsets previously wrote **no audit-log entries at all** and never set `UpdatedBy`. A new test
asserts an `AuditLog` row is written on create.

⚠️ **Before deploying:** the new FK constraint will fail to apply if any existing
`ecosystem`/`species` row references a missing entity. Check for orphans first — the local
database has zero rows, so this cannot surface in dev.

---

<a id="f2"></a>

## F2 · Only the first active role is consulted

**Category:** Authorization · **Confidence:** High — directly readable

```python
user_role = UserRoles.objects.filter(UserId=user, Status=1).select_related("RoleId").first()
if not user_role:
    return False
```

`UserRoles` is a many-to-many table — the schema permits a user to hold several active roles
— but resolution reads exactly one, with **no `order_by`**. Privileges are therefore not the
union of the user's roles, and which role wins is whatever the database returns first.

**Failure scenario.** A user is granted both `Manager` and a narrow custom role. If the
custom role is returned first, their Manager privileges silently vanish. Because there is no
`order_by`, the effective role can change between queries after a table rewrite (`VACUUM
FULL`, a restore, a bulk update) with no data change at all — the same user gets different
permissions on different days.

**To confirm:** whether multiple concurrent active roles are intended to be possible. If they
are not, a uniqueness constraint on `(UserId, Status=1)` would make the invariant explicit
and turn a silent mis-resolution into a database error. If they are, resolution needs to
union across roles.

**Resolution (2026-08-21).** `_resolve_privilege` now unions across every active role
(`RoleId__in=role_ids`), matching what `IsEntityAdmin`/`IsManagerOrAbove` already did. The
user-override branch is untouched — its `order_by("-OverrideAction")` is load-bearing.

No `UniqueConstraint` was added, deliberately: the union makes multi-role well-defined, and
such a migration could fail against pre-existing duplicate rows. `assign_role` is now wrapped
in `transaction.atomic()` so its retire-then-create pair cannot interleave. A regression test
gives one user two active roles and asserts both roles' privileges resolve — before the fix
exactly one of those assertions would have failed, depending on which row `.first()` returned.

---

<a id="f3"></a>

## F3 · `verify_record()` has no double-verification guard

**Category:** Data integrity · **Confidence:** High — stated in the function's own docstring

> *"Advance VerificationStatus to VERIFIED (3). Records verifier identity and timestamp.
> **Caller must check current status before calling — this function does not guard against
> double-verification.**"*

The guard is implemented in `EmissionsDataViewSet`, not in the service.

**Failure scenario.** Any second call — a retried request, a management command, a future
bulk-verify endpoint, a Celery task — overwrites `VerifiedBy`, `VerifiedAt` and
`VerificationNotes` with the second caller's identity. The original verifier's attestation is
lost, with no audit record of the change, which is precisely the field an assurance provider
would rely on.

**To confirm:** whether the guard belongs in the service instead, so every call site inherits
it. The docstring suggests the author considered this and chose the caller-checks contract
deliberately.

**Resolution (2026-08-21).** `verify_record()` now raises
`ValidationError({"code": "already_verified"})` when `VerificationStatus >= 3`, so every call
site inherits the guard rather than only the viewset. The view's own check is retained
deliberately — it returns the exact response body existing tests assert on, so the API is
unchanged. A new test calls the service directly twice and asserts `VerifiedBy`/`VerifiedAt`
survive the second call.

---

<a id="f4"></a>

## F4 · `report_failed` is sent before the retry is attempted

**Category:** UX / async · **Confidence:** High — ordering is explicit in the task body

```python
job.JobStatus = 4          # Failed
job.save(...)
_notify_failed(job, str(exc))
...
raise self.retry(exc=exc)  # up to 2 retries, 60s apart
```

The job is marked `Failed` and the user notified, and only then is the retry raised.

**Failure scenario.** A transient S3 timeout on attempt 1 sends the user a
"Report generation failed" notification. Attempt 2 succeeds 60 seconds later and sends
"Report ready". The user has received a failure notice for a report that worked — and, if
they act on the first message, may re-request a report that was already being generated.

**To confirm:** whether this is intended. Deferring `_notify_failed()` until
`self.request.retries >= self.max_retries` would notify only on terminal failure. Note the
status write itself is arguably correct as-is — `JobStatus = 4` between attempts is an honest
description of the job's state; it is the *notification* that is premature.

**Resolution (2026-08-21).** `_notify_failed()` now fires only when
`self.request.retries >= self.max_retries`. The `JobStatus = 4` write still happens on every
attempt — "Failed" is an honest description of the job's state between attempts; it was only
the *notification* that was premature. Three tests cover retries-remaining, terminal attempt,
and the happy path.

---

<a id="f5"></a>

## F5 · The feature gate returns 402, which `CLAUDE.md` does not state

**Category:** Documentation drift · **Confidence:** High

`CLAUDE.md` documents the gate response body:

> `{"code": "feature_gated", "feature": "...", "upgrade_url": "/pricing"}`

but not its status code. The implementation raises `FeatureGatedException` carrying
`status_code = status.HTTP_402_PAYMENT_REQUIRED`, converted to a response by the handler in
`apps/shared/exceptions.py`.

**Failure scenario.** A reviewer, or a frontend developer writing an interceptor, assumes the
platform's conventional 403 and writes a handler that never fires. The upgrade modal silently
fails to appear, and the user sees a generic error.

**To confirm:** nothing about the code — 402 Payment Required is the right choice for a
billing gate. This is a one-line documentation fix in `CLAUDE.md`.

**Resolution (2026-08-21).** `CLAUDE.md` now states the gate returns **HTTP 402 Payment
Required** and includes the `detail` key the handler actually returns — the original example
omitted it, a second inaccuracy in the same line.

---

<a id="f6"></a>

## F6 · Tasks in `tasks/` require an explicit import to be registered

**Category:** Operational · **Confidence:** High — the constraint is commented in the source

The Celery task modules live in a top-level `tasks/` package rather than inside Django apps,
so `app.autodiscover_tasks()` does not find them. `config/celery.py` compensates by importing
all eight modules explicitly.

**Failure scenario.** A developer adds `tasks/foo.py`, registers it in `beat_schedule`, and
deploys. Beat dutifully publishes the task to the queue; no worker has it registered, so every
firing raises `NotRegistered` on the worker side. The schedule looks correct in Django admin
and nothing appears wrong until someone notices the job never runs.

**To confirm:** whether a startup assertion — comparing `beat_schedule` task names against
`app.tasks` — would be worth adding. It would convert a silent runtime failure into a
loud boot failure.

**Resolution (2026-08-21) — and the first attempt was wrong.** The validator was initially
hooked to `on_after_finalize`. Its own new test failed immediately, revealing that
`app.conf.imports` is a *declaration*, not an import: Celery loads those modules only when a
worker or beat process boots. At finalize the registry is still empty, so the validator
reported **all 11** scheduled tasks as unregistered — and because finalize fires in every
process that merely imports the Celery app, it would have taken down the API container too.

The working version hooks `beat_init` (this is beat's problem, not every process's) and calls
`app.loader.import_default_modules()` before comparing. Verified end to end: beat boots clean
and the receiver reports "beat_schedule validated: 11 scheduled tasks all registered". The
shared helper `check_beat_schedule_registered()` is what the CI test calls, so the test and the
runtime guard cannot drift apart.

---

<a id="f7"></a>

## F7 · Two tasks are registered but absent from `beat_schedule`

**Category:** Operational · **Confidence:** Medium — depends on the DB scheduler's contents

`tasks.auth.prune_old_notifications` and `tasks.integrations.sync_oer_fx_rates` are defined
and imported, but neither appears in `app.conf.beat_schedule`.

Both readings are plausible and the code does not distinguish them:

- **Intended.** The primary schedule is `django_celery_beat`'s `DatabaseScheduler`, and these
  two are scheduled there, or invoked manually. `sync_oer_fx_rates` in particular looks like a
  deliberate fallback for when the ECB source is unavailable.
- **Unintended.** They were meant to be scheduled and the entry was missed — in which case
  notifications accumulate without pruning indefinitely.

**Partially checked (2026-08-21).** The local database holds **zero** `PeriodicTask` rows.
That is not evidence either way — `celery_beat` has never been started in this environment, so
an empty table is expected. It does pin down the mechanism, though: `DatabaseScheduler` seeds
`PeriodicTask` from `app.conf.beat_schedule` at beat startup, which means a task absent from
`beat_schedule` receives **no row at all** and never runs unless someone adds it by hand in
Django admin. The "scheduled in the DB instead" reading therefore only holds if that manual
step was actually performed — it does not happen automatically.

**To confirm:** inspect `PeriodicTask` rows in the deployed environment, where beat has
actually run.

**Resolution (2026-08-21) — settled with evidence, not inspection.** Split by task:

- `prune_old_notifications` **was** an oversight. It is now scheduled (05:45 daily), and beat
  has synced it into the database — confirmed by querying `PeriodicTask` after startup.
- `sync_oer_fx_rates` is **correctly** unscheduled. `sync_ecb_fx_rates` already dispatches it
  via `.delay()` when the ECB source fails, and it already no-ops with a clear log line when
  `OPEN_EXCHANGE_RATES_API_KEY` is unset (it defaults to `""`). A comment in
  `config/celery.py` and a test now record that this omission is intentional.

The mechanism hypothesised earlier is confirmed: `DatabaseScheduler` seeds `PeriodicTask`
*from* `beat_schedule` at beat startup, so a task absent from the schedule gets no row at all.
`prune_old_notifications` genuinely never ran.

---

<a id="f8"></a>

## F8 · `past_due` loses gated features immediately

**Category:** Billing · **Confidence:** High — verified by reading the query

```python
sub = EntitySubscriptions.objects.select_related("PlanId").get(
    ...
    Status__in = ["active", "trialing"],
)
```

`is_feature_enabled()` resolves a subscription only in `active` or `trialing` state. A
subscription in `past_due` matches nothing, the lookup fails, and **every** gated feature is
denied — there is no grace period.

**Failure scenario.** A customer's card expires. On the first failed charge the subscription
moves to `past_due`, and their next request to any gated endpoint returns 402 with an upgrade
prompt — despite being a paying customer mid-dunning. Scope 3 entry, land parcels, offsets and
report export all stop at once. The likely support outcome is a churn conversation rather than
a card update.

**To confirm:** this is a product decision, not a bug. Most SaaS billing allows a dunning grace
window. If a grace period is wanted, adding `"past_due"` to the `Status__in` list is the whole
change — though it should probably be time-boxed against `CurrentPeriodEnd` rather than open-ended.

**Resolution (2026-08-21).** A single `get_entitled_subscription()` helper replaces the
status filter that was duplicated across `is_feature_enabled()` and `get_active_plan()`. A
`past_due` subscription keeps its entitlements while `now() <= CurrentPeriodEnd` — it paid for
the period it is in — and loses them once that passes.

`can_add_entity()`'s fail-**open** behaviour was left exactly as-is, with a comment naming the
asymmetry against the two fail-closed callers; changing it is a separate product decision. A
new `apps/billing/tests/` package covers the full status matrix, including the two boundary
cases (`past_due` with a NULL period end, and `canceled` with a future one).

---

<a id="f9"></a>

## F9 · The unlock guard lives in the view, not the service

**Category:** Authorization · **Confidence:** High — stated in the function's own docstring

> *"Only callable by SuperAdmin — **the view enforces that guard**."*

`unlock_record()` performs the privileged state change — resetting a verified emissions record
to editable — and writes the mandatory 7-year audit entry, but performs no authorization check
of its own.

**Failure scenario.** Any future call site that is not the viewset — a management command, an
admin action, a bulk-correction task — unlocks verified records with no SuperAdmin check. The
audit row is still written, so the action is traceable, but it was never authorized.

**Note.** This is the same structural pattern as **F3**: the emissions service layer
consistently places authorization and precondition checks in the view rather than the service.
That is a defensible, coherent choice — the finding is that it is *load-bearing* and undocumented
outside the docstrings, so a new call site is one easy mistake away from bypassing it.

**Resolution (2026-08-21).** `unlock_record()` now raises `PermissionDenied` when
`unlocked_by` is not a SuperAdmin — it already received the acting user, so it always had the
context to check. The guard runs before any mutation or audit write, so a rejected unlock
leaves no trace. The view's inline check is retained for its specific response body. A test
asserts the rejection writes no `Action="Unlock_Verified"` audit row.

---

<a id="f10"></a>

## F10 · The `verify` action was open to any authenticated user

**Category:** Authorization · **Found:** during the F3/F9 work, not in the original review

`EmissionsDataViewSet` sets `permission_classes = [IsAuthenticated]` at class level and the
`verify` action did not override it. Any authenticated member of the tenant could verify an
emissions record — **including the person who created it**. In an MRV/assurance product that
defeats segregation of duties: verification is the control that makes a record defensible to an
assurance provider, and self-verification makes it worthless.

**Resolution (2026-08-21).** A `get_permissions()` override now restricts `verify` to
`IsManagerOrAbove` and `unlock` to `IsSuperAdmin`, reusing the existing permission classes
rather than adding new ones. A test asserts a `staff`-role user gets 403 while the manager path
still returns 204.

**Not done:** blocking a manager from verifying their *own* record. That is a stricter policy
that could break legitimate workflows where one person both records and verifies, and it is a
product decision rather than a defect.

---

## Reading these together

F3, F9 and F10 were one architectural pattern seen three times: `apps/emissions` treated its
service functions as trusted primitives and pushed every guard up into the view. That is a
defensible choice, but it was load-bearing and undocumented outside docstrings, leaving each
new call site one easy mistake away from bypassing it. All three guards now sit in the layer
that owns the invariant, with the view checks kept so the API's responses are unchanged.

F6 and F7 were both consequences of the top-level `tasks/` package layout, and F6 is the one
worth remembering: the first fix was wrong in a way that would have broken the API container,
and only writing the test caught it.

---
*Findings derived from `backend/apps/`, `backend/tasks/`, `backend/config/` on branch
`fix/deploy-hardening`. All resolved 2026-08-21 and verified against a running stack:
219 tests passing, migration applied, Celery worker and beat booting clean.*

# Celery Tasks — SusDevOS

All async and scheduled work runs through Celery with Redis as both broker and result backend. Scheduled tasks use `django-celery-beat` with a database-backed schedule (editable via admin without redeploy).

---

## Celery Configuration

```python
# config/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery("susdевos")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {

    # ── Integration syncs ──────────────────────────────────────────────────

    "sync-ecb-fx-daily": {
        "task": "tasks.integrations.sync_ecb_fx_rates",
        "schedule": crontab(hour=17, minute=0),   # 17:00 UTC = ~18:00 CET (after ECB publishes)
        "options": {"expires": 3600},
    },

    "sync-climatiq-weekly": {
        "task": "tasks.integrations.sync_climatiq_emission_factors",
        "schedule": crontab(hour=2, minute=0, day_of_week="sunday"),
        "options": {"expires": 86400},
    },

    # NOTE: SBTi registry sync removed (out of product scope — see CLAUDE.md § Product scope).
    # A Gold Standard registry sync runs daily at 03:30 alongside Verra (see config/celery.py).

    "sync-verra-registry-daily": {
        "task": "tasks.integrations.sync_verra_registry",
        "schedule": crontab(hour=3, minute=0),
        "options": {"expires": 3600},
    },

    # Annual tasks — triggered by SuperAdmin via management command or admin action,
    # not by celery-beat (publication dates vary). Listed here for documentation.
    # "sync-defra-annual": tasks.integrations.sync_defra_emission_factors
    # "sync-epa-egrid-annual": tasks.integrations.sync_epa_egrid_factors

    # ── GHG inventory maintenance ──────────────────────────────────────────

    "recompute-stale-inventory-totals": {
        "task": "tasks.emissions.recompute_stale_inventory_totals",
        "schedule": crontab(hour=1, minute=0),    # nightly
        "options": {"expires": 7200},
    },

    "link-milestones-to-inventories": {
        "task": "tasks.emissions.link_milestone_actuals",
        "schedule": crontab(hour=1, minute=30),   # nightly, after totals recomputed
        "options": {"expires": 3600},
    },

    # ── Report purge ───────────────────────────────────────────────────────

    "purge-expired-report-files": {
        "task": "tasks.reports.purge_expired_reports",
        "schedule": crontab(hour=4, minute=0),    # nightly
        "options": {"expires": 3600},
    },

    # ── Auth maintenance ───────────────────────────────────────────────────

    "purge-expired-jwt-revocations": {
        "task": "tasks.auth.purge_expired_revoked_tokens",
        "schedule": crontab(hour=5, minute=0),    # nightly
        "options": {"expires": 3600},
    },
}
```

---

## Integration Tasks

### `sync_ecb_fx_rates` — Daily, 17:00 UTC

```python
# tasks/integrations/fx.py

import requests
from datetime import date
from apps.shared.models import ExchangeRates   # new table from 0027

CURRENCIES = ["GBP", "EUR", "AUD", "CAD", "NZD", "ZAR", "INR", "BRL", "MXN", "SGD"]

@shared_task(
    name="tasks.integrations.sync_ecb_fx_rates",
    bind=True,
    max_retries=3,
    default_retry_delay=300,   # 5 min
)
def sync_ecb_fx_rates(self):
    """
    Fetch daily EUR-based rates from ECB, convert to USD base, cache in ExchangeRates.
    ECB publishes ~16:00 CET. Task runs at 17:00 UTC to give buffer.

    Strategy:
      1. Fetch all rates vs EUR from ECB (free, no key).
      2. Get EUR/USD rate from the same response.
      3. Compute each currency's rate to USD: rate = (1/EUR_CURRENCY_rate) × EUR_USD_rate.
      4. Upsert into ExchangeRates with RateDate = today.
    """
    today = date.today().isoformat()
    created = 0
    errors = []

    for currency in CURRENCIES:
        try:
            url = (
                f"https://data-api.ecb.europa.eu/service/data/EXR/"
                f"D.{currency}.EUR.SP00.A"
                f"?startPeriod={today}&endPeriod={today}&format=jsondata"
            )
            resp = requests.get(url, timeout=10)
            if resp.status_code == 404:
                continue   # no data yet for today (published later)
            resp.raise_for_status()

            data = resp.json()
            observations = (
                data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
            )
            if not observations:
                continue
            # ECB gives EUR per currency; invert to get currency per EUR
            eur_per_currency = float(list(observations.values())[0][0])

            # Get EUR/USD for cross rate
            usd_resp = requests.get(
                "https://data-api.ecb.europa.eu/service/data/EXR/"
                f"D.USD.EUR.SP00.A?startPeriod={today}&endPeriod={today}&format=jsondata",
                timeout=10,
            )
            usd_resp.raise_for_status()
            usd_data = usd_resp.json()
            eur_per_usd = float(
                list(usd_data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"].values())[0][0]
            )

            rate_to_usd = eur_per_usd / eur_per_currency  # currency → USD

            ExchangeRates.objects.update_or_create(
                FromCurrency=currency,
                ToCurrency="USD",
                RateDate=date.today(),
                defaults={"Rate": rate_to_usd, "Source": "ECB"},
            )
            created += 1

        except Exception as exc:
            errors.append(f"{currency}: {exc}")

    if errors:
        _alert_superadmins("ECB FX sync partial failure", "\n".join(errors))

    logger.info("ECB FX sync: %d rates updated, %d errors", created, len(errors))
```

**Retry policy:** 3 retries at 5-minute intervals. If all retries fail, falls back to Open Exchange Rates API as secondary source (separate `sync_oer_fx_rates` task chained as fallback).

**Fallback task:** `sync_oer_fx_rates` — same structure using `https://openexchangerates.org/api/latest.json?app_id={key}`. Triggered automatically on ECB failure.

---

### `sync_climatiq_emission_factors` — Weekly, Sunday 02:00 UTC

```python
# tasks/integrations/climatiq.py

PRIORITY_ACTIVITIES = [
    # Electricity - location-based (top countries by user base)
    ("electricity-supply_grid-source_residual_mix", "GB", 2024),
    ("electricity-supply_grid-source_residual_mix", "US", 2024),
    ("electricity-supply_grid-source_residual_mix", "AU", 2024),
    ("electricity-supply_grid-source_residual_mix", "IN", 2024),
    ("electricity-supply_grid-source_residual_mix", "ZA", 2024),
    # Fuel combustion
    ("fuel_combustion-type_diesel",    "GB", 2024),
    ("fuel_combustion-type_petrol",    "GB", 2024),
    ("fuel_combustion-type_natural_gas", "GB", 2024),
    # Freight transport
    ("freight_vehicle-vehicle_type_hgv-fuel_source_diesel", "GB", 2024),
    # Business travel
    ("passenger_vehicle-vehicle_type_car-fuel_source_petrol-engine_size_medium-vehicle_age_na-vehicle_weight_na", "GB", 2024),
]

@shared_task(
    name="tasks.integrations.sync_climatiq_emission_factors",
    bind=True,
    max_retries=2,
    default_retry_delay=3600,
)
def sync_climatiq_emission_factors(self):
    """
    Refresh priority emission factors from Climatiq.
    Extends list based on which activity_ids are referenced by existing EmissionsData records.
    """
    from services.integrations.climatiq import sync_climatiq_ef

    # Add any activity_ids already in use but not in priority list
    in_use = EmissionFactors.objects.filter(
        ClimatiqActivityId__isnull=False
    ).values_list("ClimatiqActivityId", "CountryCode", "ApplicableYear").distinct()

    activities = list(PRIORITY_ACTIVITIES) + [
        (aid, cc, yr) for aid, cc, yr in in_use
        if (aid, cc, yr) not in PRIORITY_ACTIVITIES
    ]

    updated = 0
    for activity_id, region, year in activities:
        try:
            sync_climatiq_ef(activity_id, region, year)
            updated += 1
            time.sleep(0.1)   # rate limit guard
        except Exception as exc:
            logger.warning("Climatiq sync failed for %s/%s/%s: %s", activity_id, region, year, exc)

    logger.info("Climatiq sync complete: %d factors updated", updated)
```

---

### ~~`sync_sbti_registry`~~ — REMOVED (out of scope)

> **REMOVED — out of product scope.** SBTi was dropped in the nature/MRV + TNFD
> refocus (see CLAUDE.md § Product scope). There is no `sync_sbti_registry` task,
> no beat entry, and no `Targets.Framework`/`SBTiStatus`/`SBTiCompanyId` wiring.
> This section is retained only as a historical record of the deprecated design.

---

### `sync_verra_registry` — Daily, 03:00 UTC

```python
# tasks/integrations/verra.py

@shared_task(
    name="tasks.integrations.sync_verra_registry",
    bind=True,
    max_retries=2,
    default_retry_delay=1800,
)
def sync_verra_registry(self):
    """
    Download Verra VCS issuance table CSV and cache into VerraCredit local table.
    After sync, re-validate any EmissionsOffsets with RegistryValidationStatus='pending'.
    """
    try:
        resp = requests.get(settings.VERRA_CSV_URL, timeout=120, stream=True)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise self.retry(exc=exc)

    reader = csv.DictReader(codecs.iterdecode(resp.iter_lines(), "utf-8"))
    upserted = 0

    for row in reader:
        VerraCredit.objects.update_or_create(
            SerialNumber=row.get("Serial Number", "").strip(),
            defaults={
                "ProjectId": row.get("Project ID"),
                "ProjectName": row.get("Project Name"),
                "VintageYear": _safe_int(row.get("Vintage Year")),
                "Quantity": _safe_decimal(row.get("Quantity")),
                "RetiredAt": _parse_date(row.get("Retirement Date")),
                "RetirementBeneficiary": row.get("Retirement Beneficiary"),
                "LastSyncedAt": now(),
            }
        )
        upserted += 1

    # Re-validate pending offsets now that cache is fresh
    pending = EmissionsOffsets.objects.filter(
        RegistryValidationStatus="pending",
        CreditSerialNumber__isnull=False,
    )
    for offset in pending:
        validate_offset_against_registry.delay(offset.pk)

    logger.info("Verra sync: %d credits cached, %d offsets re-queued for validation", upserted, pending.count())
```

---

## GHG Inventory Maintenance Tasks

### `recompute_stale_inventory_totals` — Nightly, 01:00 UTC

```python
# tasks/emissions.py

@shared_task(name="tasks.emissions.recompute_stale_inventory_totals")
def recompute_stale_inventory_totals():
    """
    Find GHGInventories where TotalsLastComputedAt is NULL or older than 24h,
    and recompute Scope1/2/3 totals. Runs nightly to catch any missed invalidations.
    """
    stale_cutoff = now() - timedelta(hours=24)
    stale = GHGInventories.objects.filter(
        models.Q(TotalsLastComputedAt__isnull=True) |
        models.Q(TotalsLastComputedAt__lt=stale_cutoff),
        DeletedAt__isnull=True,
    )

    for inventory in stale:
        try:
            compute_inventory_totals(inventory.InventoryId)
        except Exception as exc:
            logger.error("Failed to recompute inventory %s: %s", inventory.InventoryId, exc)
```

### `link_milestone_actuals` — Nightly, 01:30 UTC

> **Implemented model fields** (`apps/emissions/models.TargetMilestones`): `MilestoneYear`,
> `TargetEmissionsTonnes`, `ActualEmissionsTonnes`, `IsAchieved` (bool). There is no
> `ActualInventoryId` FK or multi-tier `AchievementStatus` — the milestone is matched to its
> inventory by `(EntityId, MilestoneYear)` and achievement is a simple
> `actual <= target` boolean. The task below reflects the actual implementation.

```python
@shared_task(name="tasks.emissions.link_milestone_actuals")
def link_milestone_actuals():
    """
    For each TargetMilestone where MilestoneYear has passed and actuals not yet
    linked, find the matching computed GHGInventory and populate
    ActualEmissionsTonnes + IsAchieved.
    """
    current_year = date.today().year

    milestones = TargetMilestones.objects.filter(
        MilestoneYear__lt=current_year,
        ActualEmissionsTonnes__isnull=True,
        Status__lt=4,
    ).select_related("TargetId__EntityId")

    for milestone in milestones:
        entity = milestone.TargetId.EntityId

        inventory = GHGInventories.objects.filter(
            EntityId=entity,
            ReportingYear=milestone.MilestoneYear,
            NetEmissionsTonnes__isnull=False,   # totals computed
        ).first()

        if not inventory:
            continue

        actual = inventory.NetEmissionsTonnes or Decimal("0")
        target = milestone.TargetEmissionsTonnes

        milestone.ActualEmissionsTonnes = actual
        milestone.IsAchieved = bool(target and actual <= target)
        milestone.save(update_fields=["ActualEmissionsTonnes", "IsAchieved"])
```

---

## Report Tasks

### `generate_report` — On-demand

```python
# tasks/reports.py

@shared_task(
    name="tasks.reports.generate_report",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    time_limit=300,    # 5 min hard limit
    soft_time_limit=270,
)
def generate_report(self, report_job_id: int):
    """
    Generate a report file and upload to S3/MinIO.
    Called immediately on POST /api/reports/ — job is queued, task runs async.
    """
    job = ReportJobs.objects.get(ReportJobId=report_job_id)
    job.JobStatus = 2   # Processing
    job.CeleryTaskId = self.request.id
    job.save(update_fields=["JobStatus", "CeleryTaskId"])

    try:
        renderer = get_renderer(job.ReportType, job.Format)
        file_bytes = renderer.render(job.Parameters)

        s3_key = f"reports/{job.EntityId_id}/{job.ReportJobId}.{job.Format}"
        upload_to_storage(s3_key, file_bytes, content_type=_mime(job.Format))

        job.S3Key = s3_key
        job.JobStatus = 3   # Complete
        job.save(update_fields=["S3Key", "JobStatus"])

        Notifications.objects.create(
            EntityId=job.EntityId,
            NotificationType="report_ready",
            RelatedModule="reports",
            RelatedRecordId=job.ReportJobId,
            Message=f"Your {job.get_ReportType_display()} report is ready.",
        )

    except SoftTimeLimitExceeded:
        job.JobStatus = 4   # Failed
        job.save(update_fields=["JobStatus"])
        raise

    except Exception as exc:
        job.JobStatus = 4
        job.save(update_fields=["JobStatus"])
        Notifications.objects.create(
            EntityId=job.EntityId,
            NotificationType="report_failed",
            RelatedModule="reports",
            RelatedRecordId=job.ReportJobId,
            Message=f"Report generation failed: {exc}",
        )
        raise self.retry(exc=exc)
```

### `purge_expired_reports` — Nightly, 04:00 UTC

```python
@shared_task(name="tasks.reports.purge_expired_reports")
def purge_expired_reports():
    """Delete S3 objects and DB records for reports past PurgeAfter date."""
    expired = ReportJobs.objects.filter(
        PurgeAfter__lt=now(),
        JobStatus=3,   # Complete only — don't purge failed jobs (may need investigation)
    )
    for job in expired:
        if job.S3Key:
            delete_from_storage(job.S3Key)
        job.delete()
    logger.info("Purged %d expired report files", expired.count())
```

---

## Auth Maintenance Tasks

### `purge_expired_revoked_tokens` — Nightly, 05:00 UTC

```python
# tasks/auth.py

@shared_task(name="tasks.auth.purge_expired_revoked_tokens")
def purge_expired_revoked_tokens():
    """
    Remove RevokedTokens entries whose ExpiresAt has passed.
    These tokens are already expired so the revocation list entry is redundant.
    Keeps the revocation table lean — important for auth middleware lookup performance.
    """
    deleted, _ = RevokedTokens.objects.filter(ExpiresAt__lt=now()).delete()
    logger.info("Purged %d expired JWT revocation entries", deleted)
```

---

## Retry and Error Policy

| Failure type | Behaviour |
|-------------|-----------|
| Network error (timeout, connection refused) | Retry with exponential backoff up to max_retries |
| 4xx client error | No retry — log + alert SuperAdmin |
| 5xx server error | Retry as above |
| Task hard time limit exceeded | Mark job Failed, alert SuperAdmin |
| All retries exhausted | Create `Notifications` record (type=`system_error`) for all SuperAdmin users |

### Alerting helper

```python
def _alert_superadmins(subject: str, body: str):
    from apps.users.models import Users
    from apps.notifications.models import Notifications

    superadmins = Users.objects.filter(Role__RoleName="SuperAdmin", Status=1)
    for admin in superadmins:
        Notifications.objects.create(
            UserId=admin,
            NotificationType="system_error",
            Message=f"{subject}: {body[:500]}",
        )
```

---

## Queue Configuration

Use separate queues to prevent slow integration tasks from blocking user-facing report jobs:

```python
# config/celery.py — additional queue routing

app.conf.task_routes = {
    "tasks.integrations.*":    {"queue": "integrations"},
    "tasks.reports.*":         {"queue": "reports"},
    "tasks.emissions.*":       {"queue": "default"},
    "tasks.auth.*":            {"queue": "default"},
}

# Worker startup commands:
# celery -A config.celery worker -Q default -c 4
# celery -A config.celery worker -Q integrations -c 2
# celery -A config.celery worker -Q reports -c 2 --max-tasks-per-child 10  (WeasyPrint memory management)
# celery -A config.celery beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Environment Variables Added

```bash
# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Integration tasks — all managed in .env, no redeploy needed to update URLs
SBTI_COMPANIES_CSV_URL=
DEFRA_EF_SPREADSHEET_URL=
EPA_EGRID_URL=
VERRA_CSV_URL=
GOLD_STANDARD_REGISTRY_URL=
```

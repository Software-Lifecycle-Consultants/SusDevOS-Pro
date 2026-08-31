"""
Celery application configuration for SusDevOS.
Workers: default queue (general), integrations queue, reports queue.
Beat: DatabaseScheduler (schedule stored in DB, editable via admin).
"""

import logging
import os

from django.core.exceptions import ImproperlyConfigured

from celery import Celery
from celery.schedules import crontab
from celery.signals import beat_init

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("susdevos")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# The task modules live in a top-level ``tasks/`` package (not inside Django apps),
# so autodiscover_tasks() does not find them. Import them explicitly so every task
# referenced in beat_schedule is registered with the worker.
app.conf.imports = (
    "tasks.emissions",
    "tasks.reports",
    "tasks.auth",
    "tasks.billing",
    "tasks.integrations.fx",
    "tasks.integrations.verra",
    "tasks.integrations.gold_standard",
    "tasks.integrations.climatiq",
    "tasks.integrations.defra",
)

# ── Beat schedule ─────────────────────────────────────────────────────────────
# Primary schedule is stored in the DB (django_celery_beat), which allows
# editing via admin without redeploy. This dict is the initial seed.

app.conf.beat_schedule = {

    # Integration syncs
    "sync-ecb-fx-daily": {
        "task": "tasks.integrations.sync_ecb_fx_rates",
        "schedule": crontab(hour=17, minute=0),
        "options": {"expires": 3600},
    },
    "sync-climatiq-weekly": {
        "task": "tasks.integrations.sync_climatiq_emission_factors",
        "schedule": crontab(hour=2, minute=0, day_of_week="sunday"),
        "options": {"expires": 86400},
    },
    # DEFRA publishes each June and revises within a month or two, so this runs
    # mid-July. It is the only factor source that needs no API key, and the only
    # one that can populate an empty library.
    "import-defra-factors-annually": {
        "task": "tasks.integrations.sync_defra_emission_factors",
        "schedule": crontab(hour=4, minute=0, day_of_month=15, month_of_year=7),
        "options": {"expires": 86400},
    },
    "sync-verra-registry-daily": {
        "task": "tasks.integrations.sync_verra_registry",
        "schedule": crontab(hour=3, minute=0),
        "options": {"expires": 3600},
    },
    "sync-gold-standard-registry-daily": {
        "task": "tasks.integrations.sync_gold_standard_registry",
        "schedule": crontab(hour=3, minute=30),
        "options": {"expires": 3600},
    },
    # tasks.integrations.sync_oer_fx_rates is intentionally NOT scheduled here.
    # It's a manual fallback for when the ECB source is unavailable and requires
    # OPEN_EXCHANGE_RATES_API_KEY, which defaults to "" (settings/base.py:260).
    # sync_ecb_fx_rates() already triggers it on ECB failure via .delay(); it stays
    # off beat_schedule so it isn't run daily against an unset API key.

    # GHG maintenance
    "recompute-stale-inventory-totals": {
        "task": "tasks.emissions.recompute_stale_inventory_totals",
        "schedule": crontab(hour=1, minute=0),
        "options": {"expires": 7200},
    },
    "link-milestones-to-inventories": {
        "task": "tasks.emissions.link_milestone_actuals",
        "schedule": crontab(hour=1, minute=30),
        "options": {"expires": 3600},
    },

    # Housekeeping
    "purge-expired-report-files": {
        "task": "tasks.reports.purge_expired_reports",
        "schedule": crontab(hour=4, minute=0),
        "options": {"expires": 3600},
    },
    "purge-expired-jwt-revocations": {
        "task": "tasks.auth.purge_expired_revoked_tokens",
        "schedule": crontab(hour=5, minute=0),
        "options": {"expires": 3600},
    },
    "purge-expired-audit-logs": {
        "task": "tasks.auth.purge_expired_audit_logs",
        "schedule": crontab(hour=5, minute=30),
        "options": {"expires": 3600},
    },
    "prune-old-notifications": {
        "task": "tasks.auth.prune_old_notifications",
        "schedule": crontab(hour=5, minute=45),
        "options": {"expires": 3600},
    },
    "reset-api-call-counters": {
        "task": "tasks.billing.reset_daily_api_counters",
        "schedule": crontab(hour=0, minute=0),   # midnight UTC
        "options": {"expires": 3600},
    },
}

# ── Queue routing ─────────────────────────────────────────────────────────────

app.conf.task_routes = {
    "tasks.integrations.*": {"queue": "integrations"},
    "tasks.reports.*":      {"queue": "reports"},
    "tasks.emissions.*":    {"queue": "default"},
    "tasks.auth.*":         {"queue": "default"},
    "tasks.billing.*":      {"queue": "default"},
}


def check_beat_schedule_registered():
    """Return the beat_schedule task names that are not in the task registry.

    ``app.conf.imports`` above is a *declaration*, not an import: Celery only
    loads those modules when a worker or beat process boots. So the registry is
    empty until ``import_default_modules()`` runs, and this must force it before
    comparing — otherwise every scheduled task looks unregistered.
    """
    app.loader.import_default_modules()
    return sorted(
        entry["task"]
        for entry in app.conf.beat_schedule.values()
        if entry["task"] not in app.tasks
    )


@beat_init.connect
def _validate_beat_schedule(sender=None, **kwargs):
    """Fail beat startup when beat_schedule names a task no worker can run.

    Tasks live in the top-level ``tasks/`` package, which autodiscover_tasks()
    does not scan — they are imported explicitly via ``app.conf.imports``.
    Forgetting that import leaves beat publishing a task every worker rejects as
    NotRegistered, with nothing obviously wrong in the schedule itself.

    Hooked to ``beat_init`` rather than ``on_after_finalize`` deliberately: this
    is beat's problem, and finalize fires in every process that merely imports
    the Celery app (the API included), where raising would take down a container
    that has nothing to do with scheduling.
    """
    missing = check_beat_schedule_registered()
    if missing:
        raise ImproperlyConfigured(
            f"beat_schedule references unregistered tasks: {missing}. "
            f"Add the owning module to app.conf.imports in config/celery.py."
        )
    logger.info(
        "beat_schedule validated: %d scheduled tasks all registered.",
        len(app.conf.beat_schedule),
    )

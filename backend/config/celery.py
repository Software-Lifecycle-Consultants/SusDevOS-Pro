"""
Celery application configuration for SusDevOS.
Workers: default queue (general), integrations queue, reports queue.
Beat: DatabaseScheduler (schedule stored in DB, editable via admin).
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("susdevos")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

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
    "sync-sbti-registry-monthly": {
        "task": "tasks.integrations.sync_sbti_registry",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),
        "options": {"expires": 86400},
    },
    "sync-verra-registry-daily": {
        "task": "tasks.integrations.sync_verra_registry",
        "schedule": crontab(hour=3, minute=0),
        "options": {"expires": 3600},
    },

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

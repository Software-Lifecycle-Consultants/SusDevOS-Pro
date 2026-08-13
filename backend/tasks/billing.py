"""Billing housekeeping — reset daily API call counters at midnight UTC."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="tasks.billing.reset_daily_api_counters")
def reset_daily_api_counters():
    """Reset UsageTracking.ApiCallsToday to 0 for all entities. Runs at 00:00 UTC."""
    from apps.billing.models import UsageTracking

    updated = UsageTracking.objects.filter(ApiCallsToday__gt=0).update(ApiCallsToday=0)
    logger.info("reset_daily_api_counters: reset %d entity counters", updated)
    return {"reset": updated}


# Note: prune_old_notifications task was moved to tasks/auth.py (correct module)

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


@shared_task(name="tasks.billing.prune_old_notifications")
def prune_old_notifications():
    """Keep max 100 notifications per user — prune oldest beyond that."""
    from django.db import connection

    with connection.cursor() as cur:
        # Delete notifications beyond rank 100 per user (ordered by CreatedAt desc)
        cur.execute("""
            DELETE FROM notifications
            WHERE "NotificationId" IN (
                SELECT "NotificationId"
                FROM (
                    SELECT "NotificationId",
                           ROW_NUMBER() OVER (
                               PARTITION BY "UserId_id"
                               ORDER BY "CreatedAt" DESC
                           ) AS rn
                    FROM notifications
                ) ranked
                WHERE rn > 100
            )
        """)
        deleted = cur.rowcount

    logger.info("prune_old_notifications: removed %d rows", deleted)
    return {"deleted": deleted}

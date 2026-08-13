"""
Auth housekeeping tasks.

Purge expired entries from RevokedTokens and AuditLog to keep the tables lean.
Both tasks run nightly; AuditLog purge respects per-row RetentionTier.
"""
import logging
from datetime import timedelta

from django.utils.timezone import now

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="tasks.auth.purge_expired_revoked_tokens")
def purge_expired_revoked_tokens():
    """Remove RevokedTokens rows whose JWT has naturally expired (ExpiresAt < now)."""
    from apps.users.models import RevokedTokens

    deleted, _ = RevokedTokens.objects.filter(ExpiresAt__lt=now()).delete()
    logger.info("purge_expired_revoked_tokens: deleted %d rows", deleted)
    return {"deleted": deleted}


@shared_task(name="tasks.auth.purge_expired_audit_logs")
def purge_expired_audit_logs():
    """
    Remove AuditLog rows according to their RetentionTier:
      1 → 30 days   (access-denied, high-volume)
      2 → 1 year    (login/session)
      3 → 7 years   (CRUD, emissions, user management — regulatory)
    """
    from apps.shared.models import AuditLog

    cutoffs = {
        1: now() - timedelta(days=30),
        2: now() - timedelta(days=365),
        3: now() - timedelta(days=365 * 7),
    }
    total = 0
    for tier, cutoff in cutoffs.items():
        deleted, _ = AuditLog.objects.filter(
            RetentionTier=tier, ChangedOn__lt=cutoff
        ).delete()
        total += deleted

    logger.info("purge_expired_audit_logs: deleted %d rows total", total)
    return {"deleted": total}


@shared_task(name="tasks.auth.prune_old_notifications")
def prune_old_notifications():
    """Keep max 100 notifications per user — delete oldest beyond that limit."""
    from django.db.models import OuterRef, Subquery

    from apps.notifications.models import Notifications

    # ORM approach: find the 101st notification (by CreatedAt desc) per user and
    # delete everything older than it.
    keep_threshold = (
        Notifications.objects
        .filter(UserId_id=OuterRef("UserId_id"))
        .order_by("-CreatedAt")
        .values("CreatedAt")[100:101]
    )
    deleted, _ = (
        Notifications.objects
        .filter(CreatedAt__lt=Subquery(keep_threshold))
        .delete()
    )
    logger.info("prune_old_notifications: removed %d rows", deleted)
    return {"deleted": deleted}

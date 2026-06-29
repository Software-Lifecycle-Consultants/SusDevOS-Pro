"""
Notification service layer.

Single helper for emitting in-app notifications so business logic does not
construct Notifications rows directly. Never raises — a notification failure
must not break the underlying operation (it is logged instead).
"""
import logging

logger = logging.getLogger(__name__)


def notify(*, user_id, entity_id, type, title, body,
           related_module=None, related_record_id=None):
    """
    Create one Notifications row. ``type`` must be a value from
    NOTIFICATION_TYPE_CHOICES. No-ops (with a log) if user_id is missing.
    """
    if not user_id:
        return
    from apps.notifications.models import Notifications

    try:
        Notifications.objects.create(
            UserId_id       = user_id,
            EntityId_id     = entity_id,
            Type            = type,
            Title           = title,
            Body            = body,
            RelatedModule   = related_module,
            RelatedRecordId = related_record_id,
        )
    except Exception as exc:  # never let a notification break the request
        logger.error("notify failed (type=%s user=%s): %s", type, user_id, exc)

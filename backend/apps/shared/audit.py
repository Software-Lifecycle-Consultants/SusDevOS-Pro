"""
Centralized audit-log helper.

Single entry point for writing AuditLog rows so business logic and views never
construct AuditLog directly (the model docstring mandates this). Mutations that
must be auditable call ``audit_log(...)``; the TenantViewSetMixin calls it
automatically for create/update/soft-delete on every tenant-scoped ViewSet.

RetentionTier: 1 = 30-day, 2 = 1-year (auth/session), 3 = 7-year (CRUD/regulatory).
CRUD on domain records is regulatory evidence, so it defaults to tier 3.
"""
import logging

logger = logging.getLogger(__name__)


def audit_log(*, action, table_name=None, record_id=None, description=None,
              entity_id=None, user=None, request=None, old_values=None,
              new_values=None, retention_tier=3):
    """
    Write one AuditLog row. Never raises — an audit failure must not break the
    underlying business operation (it is logged instead).

    Pass either ``user`` directly or a ``request`` (user + IP + UA are derived).
    """
    from apps.shared.models import AuditLog

    if request is not None:
        if user is None:
            user = getattr(request, "user", None)
        if entity_id is None:
            entity_id = getattr(request, "entity_id", None)

    user = user if (user is not None and getattr(user, "is_authenticated", False)) else None
    username = getattr(user, "username", None) if user else None
    ip = _client_ip(request) if request is not None else None
    ua = request.META.get("HTTP_USER_AGENT", "")[:500] if request is not None else None

    try:
        AuditLog.objects.create(
            EntityId_id       = entity_id,
            ChangedBy         = user,
            ChangedByUsername = username,
            Action            = action,
            TableName         = table_name,
            RecordId          = record_id,
            Description       = description,
            OldValues         = old_values,
            NewValues         = new_values,
            IpAddress         = ip,
            UserAgent         = ua,
            RetentionTier     = retention_tier,
        )
    except Exception as exc:  # never let auditing break the request
        logger.error("audit_log write failed (action=%s table=%s id=%s): %s",
                     action, table_name, record_id, exc)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()[:45]
    addr = request.META.get("REMOTE_ADDR")
    return addr[:45] if addr else None

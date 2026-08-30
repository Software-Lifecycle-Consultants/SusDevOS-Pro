"""
Billing service layer.

Feature gate resolution lives here so it can be called from Celery tasks,
management commands, and anywhere else that needs a plan check without an
HTTP request object.
"""
from django.conf import settings
from django.utils import timezone

ENTITLED_STATUSES = ("active", "trialing")


def get_entitled_subscription(*, entity_id: int):
    """The subscription that currently confers plan entitlements, or None.

    ``past_due`` keeps its entitlements until the end of the period it has
    already paid for — a failed card should not cut off access mid-period.
    Once ``CurrentPeriodEnd`` passes, entitlements stop.
    """
    from apps.billing.models import EntitySubscriptions

    try:
        sub = EntitySubscriptions.objects.select_related("PlanId").get(EntityId_id=entity_id)
    except EntitySubscriptions.DoesNotExist:
        return None
    if sub.Status in ENTITLED_STATUSES:
        return sub
    if sub.Status == "past_due" and sub.CurrentPeriodEnd and timezone.now() <= sub.CurrentPeriodEnd:
        return sub
    return None


def feature_gates_enforced() -> bool:
    """Whether per-capability feature gating is switched on.

    Default OFF (settings.FEATURE_GATES_ENABLED): plans are sold on service and
    hosting tiers, not on which capabilities unlock. Read from settings on every
    call rather than captured at import, so tests and any future reintroduction
    can toggle it with override_settings.
    """
    return bool(getattr(settings, "FEATURE_GATES_ENABLED", False))


def is_feature_enabled(*, entity_id: int, feature_key: str) -> bool:
    """
    Return True if the entity's active subscription includes the feature.
    Returns False for unknown entities, no active subscription, or gated features.
    SuperAdmin bypass is NOT applied here — callers handle that check.

    When gating is switched off every feature reads as enabled, for every caller
    including Celery tasks and management commands. Plan *limits* are unaffected:
    they resolve through get_active_plan(), not this function.
    """
    from apps.billing.models import PlanFeatures

    if not feature_gates_enforced():
        return True

    sub = get_entitled_subscription(entity_id=entity_id)
    if sub is None:
        return False

    return PlanFeatures.objects.filter(
        PlanId     = sub.PlanId,
        FeatureKey = feature_key,
        IsEnabled  = True,
    ).exists()


def get_active_plan(*, entity_id: int):
    """
    Return the Plan instance for the entity's active/trialing (or in-grace
    past_due) subscription, or None if no entitled subscription exists.
    """
    sub = get_entitled_subscription(entity_id=entity_id)
    return sub.PlanId if sub else None


def get_upgrade_message(*, feature_key: str) -> str:
    """Return the stored upgrade prompt for a feature, with a safe fallback."""
    from apps.billing.models import PlanFeatures

    feature = PlanFeatures.objects.filter(FeatureKey=feature_key).order_by("PlanId").first()
    return feature.UpgradeMessage if feature else f"Feature '{feature_key}' requires a higher plan."


# ── Plan-limit enforcement (G8) ────────────────────────────────────────────────
#
# These encapsulate the limit-comparison logic that was previously missing
# (limits were stored but never compared; ApiCallsToday was reset but never
# incremented). They are wired into the programmatic-API path. Note that the
# daily counter is meant for *API-key* traffic, NOT browser/JWT requests, so
# record_api_call() must only be invoked from the API-key authentication backend.

def record_api_call(*, entity_id: int) -> dict:
    """
    Increment today's API-call counter for the entity and report whether it is
    within the plan's MaxApiCallsPerDay limit.

    Returns: {"allowed": bool, "calls_today": int, "limit": int}.
    Semantics (per Plans.MaxApiCallsPerDay help_text): limit 0 == no API access.
    """
    from datetime import date as _date

    from django.db.models import F

    from apps.billing.models import UsageTracking

    plan = get_active_plan(entity_id=entity_id)
    limit = getattr(plan, "MaxApiCallsPerDay", 0) if plan else 0

    usage, _ = UsageTracking.objects.get_or_create(
        EntityId_id=entity_id,
        PeriodStart=_date.today(),
        defaults={"ApiCallsToday": 0},
    )
    # Atomic increment to avoid lost updates under concurrency.
    UsageTracking.objects.filter(pk=usage.pk).update(ApiCallsToday=F("ApiCallsToday") + 1)
    usage.refresh_from_db(fields=["ApiCallsToday"])

    allowed = limit > 0 and usage.ApiCallsToday <= limit
    return {"allowed": allowed, "calls_today": usage.ApiCallsToday, "limit": limit}


def can_add_entity(*, entity_id: int) -> bool:
    """
    Whether the subscription tied to ``entity_id`` permits provisioning another
    entity (MaxEntities; 0 == unlimited). Returns True when no active plan is
    found so platform/SuperAdmin provisioning is never blocked by a missing sub.
    """
    from apps.entities.models import Entities

    # Routed through get_active_plan() (→ get_entitled_subscription()) for
    # consistency with is_feature_enabled()/record_api_call(), but this function
    # fails OPEN when no plan resolves — the opposite of those two, which fail
    # closed. That asymmetry is intentional and pre-existing (unmetered entity
    # provisioning is treated differently from feature/usage gating); changing
    # it is a separate product decision, not part of this fix.
    plan = get_active_plan(entity_id=entity_id)
    if plan is None:
        return True
    max_entities = getattr(plan, "MaxEntities", 0)
    if not max_entities:  # 0 == unlimited
        return True
    active_count = Entities.objects.filter(Status__lt=4).count()
    return active_count < max_entities

"""
Billing service layer.

Feature gate resolution lives here so it can be called from Celery tasks,
management commands, and anywhere else that needs a plan check without an
HTTP request object.
"""


def is_feature_enabled(*, entity_id: int, feature_key: str) -> bool:
    """
    Return True if the entity's active subscription includes the feature.
    Returns False for unknown entities, no active subscription, or gated features.
    SuperAdmin bypass is NOT applied here — callers handle that check.
    """
    from apps.billing.models import EntitySubscriptions, PlanFeatures

    try:
        sub = EntitySubscriptions.objects.select_related("PlanId").get(
            EntityId_id = entity_id,
            Status__in  = ["active", "trialing"],
        )
    except EntitySubscriptions.DoesNotExist:
        return False

    return PlanFeatures.objects.filter(
        PlanId     = sub.PlanId,
        FeatureKey = feature_key,
        IsEnabled  = True,
    ).exists()


def get_active_plan(*, entity_id: int):
    """
    Return the Plan instance for the entity's active/trialing subscription,
    or None if no active subscription exists.
    """
    from apps.billing.models import EntitySubscriptions

    try:
        sub = EntitySubscriptions.objects.select_related("PlanId").get(
            EntityId_id = entity_id,
            Status__in  = ["active", "trialing"],
        )
        return sub.PlanId
    except EntitySubscriptions.DoesNotExist:
        return None


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

    plan = get_active_plan(entity_id=entity_id)
    if plan is None:
        return True
    max_entities = getattr(plan, "MaxEntities", 0)
    if not max_entities:  # 0 == unlimited
        return True
    active_count = Entities.objects.filter(Status__lt=4).count()
    return active_count < max_entities

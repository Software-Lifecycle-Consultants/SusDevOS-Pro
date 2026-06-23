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

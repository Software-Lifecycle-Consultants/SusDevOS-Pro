"""
Regression tests for FIX F8: ``past_due`` subscriptions must keep their
entitlements until ``CurrentPeriodEnd`` instead of losing every gated feature
the instant a payment fails.

Covers ``is_feature_enabled()`` across the full ``EntitySubscriptions.Status``
matrix (active, trialing, past_due — in and out of grace, canceled, and no
subscription row at all), plus the plan-does-not-have-the-feature case.
"""
from datetime import timedelta

from django.utils import timezone

import pytest

from apps.billing.services import is_feature_enabled

pytestmark = pytest.mark.django_db

FEATURE_KEY = "carbon_offsets"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_plan(feature_key=FEATURE_KEY, *, feature_enabled=True):
    """A Plan with a single PlanFeatures row for ``feature_key``."""
    from apps.billing.models import PlanFeatures, Plans

    plan = Plans.objects.create(
        PlanKey="entitlement_test_plan",
        PlanName="Entitlement Test Plan",
        PriceMonthlyGBP=0,
        PriceAnnualGBP=0,
        MaxEntities=0,
        MaxUsersPerEntity=0,
        MaxReportingYears=0,
        SupportTier="standard",
    )
    PlanFeatures.objects.create(
        PlanId=plan,
        FeatureKey=feature_key,
        IsEnabled=feature_enabled,
        UpgradeMessage="Upgrade to use this feature.",
    )
    return plan


def _make_subscription(entity, plan, *, status, current_period_end=None):
    from apps.billing.models import EntitySubscriptions

    return EntitySubscriptions.objects.create(
        EntityId=entity,
        PlanId=plan,
        Status=status,
        CurrentPeriodEnd=current_period_end,
    )


# ── is_feature_enabled() across the status matrix ───────────────────────────


class TestIsFeatureEnabledStatusMatrix:
    def test_active_subscription_with_feature_is_enabled(self, entity):
        plan = _make_plan()
        _make_subscription(entity, plan, status="active")

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_trialing_subscription_with_feature_is_enabled(self, entity):
        plan = _make_plan()
        _make_subscription(entity, plan, status="trialing")

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_past_due_with_future_period_end_is_enabled(self, entity):
        """Grace period: a failed card should not cut off access mid-period."""
        plan = _make_plan()
        _make_subscription(
            entity, plan, status="past_due",
            current_period_end=timezone.now() + timedelta(days=5),
        )

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_past_due_with_past_period_end_is_denied(self, entity):
        plan = _make_plan()
        _make_subscription(
            entity, plan, status="past_due",
            current_period_end=timezone.now() - timedelta(days=1),
        )

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_past_due_with_null_period_end_is_denied(self, entity):
        plan = _make_plan()
        _make_subscription(entity, plan, status="past_due", current_period_end=None)

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_canceled_is_denied(self, entity):
        plan = _make_plan()
        _make_subscription(
            entity, plan, status="canceled",
            current_period_end=timezone.now() + timedelta(days=5),
        )

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_no_subscription_row_is_denied(self, entity):
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_active_subscription_without_the_feature_is_denied(self, entity):
        plan = _make_plan(feature_key="some_other_feature")
        _make_subscription(entity, plan, status="active")

        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

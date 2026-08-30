"""
Entitlement resolution across the ``EntitySubscriptions.Status`` matrix.

Originally a regression test for FIX F8: ``past_due`` subscriptions must keep
their entitlements until ``CurrentPeriodEnd`` instead of losing everything the
instant a payment fails.

That policy still holds, but what it governs has changed. Per-capability feature
gating is switched off (settings.FEATURE_GATES_ENABLED, default False) now that
plans are sold on service and hosting tiers, so ``is_feature_enabled()`` is open
to everyone. The grace period now lives entirely in
``get_entitled_subscription()`` / ``get_active_plan()``, which are what the plan
limits resolve through.

Note those limits are not enforced yet: ``can_add_entity()`` and
``record_api_call()`` have no callers. So this file asserts the status matrix
directly against the resolver rather than through a caller, which also keeps the
policy pinned for whenever the limits are wired up.
"""
from datetime import timedelta

from django.utils import timezone

import pytest

from apps.billing.services import (
    get_active_plan,
    get_entitled_subscription,
    is_feature_enabled,
)

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


# ── The live path: which subscription confers plan limits ────────────────────


class TestEntitledSubscriptionStatusMatrix:
    """``get_entitled_subscription()`` is unaffected by the feature-gate switch.

    It decides whether a plan's quantitative limits apply, so the F8 grace
    period is asserted here rather than through ``is_feature_enabled()``.
    """

    def test_active_subscription_is_entitled(self, entity):
        _make_subscription(entity, _make_plan(), status="active")
        assert get_entitled_subscription(entity_id=entity.EntityId) is not None

    def test_trialing_subscription_is_entitled(self, entity):
        _make_subscription(entity, _make_plan(), status="trialing")
        assert get_entitled_subscription(entity_id=entity.EntityId) is not None

    def test_past_due_within_grace_is_entitled(self, entity):
        """A failed card must not cut off access mid-period (FIX F8)."""
        _make_subscription(
            entity, _make_plan(), status="past_due",
            current_period_end=timezone.now() + timedelta(days=5),
        )
        assert get_entitled_subscription(entity_id=entity.EntityId) is not None

    def test_past_due_after_period_end_is_not_entitled(self, entity):
        _make_subscription(
            entity, _make_plan(), status="past_due",
            current_period_end=timezone.now() - timedelta(days=1),
        )
        assert get_entitled_subscription(entity_id=entity.EntityId) is None

    def test_past_due_with_null_period_end_is_not_entitled(self, entity):
        _make_subscription(entity, _make_plan(), status="past_due", current_period_end=None)
        assert get_entitled_subscription(entity_id=entity.EntityId) is None

    def test_canceled_is_not_entitled(self, entity):
        _make_subscription(
            entity, _make_plan(), status="canceled",
            current_period_end=timezone.now() + timedelta(days=5),
        )
        assert get_entitled_subscription(entity_id=entity.EntityId) is None

    def test_no_subscription_row_is_not_entitled(self, entity):
        assert get_entitled_subscription(entity_id=entity.EntityId) is None

    def test_get_active_plan_follows_the_same_matrix(self, entity):
        plan = _make_plan()
        sub = _make_subscription(entity, plan, status="active")
        assert get_active_plan(entity_id=entity.EntityId) == plan

        sub.Status = "canceled"
        sub.save(update_fields=["Status"])
        assert get_active_plan(entity_id=entity.EntityId) is None


# ── Default: gating is off, so every feature reads as enabled ────────────────


class TestFeatureGatingIsOffByDefault:
    def test_no_subscription_still_has_every_feature(self, entity):
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_canceled_subscription_still_has_every_feature(self, entity):
        _make_subscription(entity, _make_plan(), status="canceled")
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_a_key_no_plan_defines_is_still_enabled(self, entity):
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key="never_seeded") is True


# ── The kept machinery: the matrix as it behaves with the switch on ──────────


class TestIsFeatureEnabledWhenGatingIsSwitchedOn:
    """Guards the switched-off code path against rot."""

    @pytest.fixture(autouse=True)
    def _enforce(self, settings):
        settings.FEATURE_GATES_ENABLED = True

    def test_active_subscription_with_feature_is_enabled(self, entity):
        _make_subscription(entity, _make_plan(), status="active")
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_trialing_subscription_with_feature_is_enabled(self, entity):
        _make_subscription(entity, _make_plan(), status="trialing")
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_past_due_with_future_period_end_is_enabled(self, entity):
        _make_subscription(
            entity, _make_plan(), status="past_due",
            current_period_end=timezone.now() + timedelta(days=5),
        )
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is True

    def test_past_due_with_past_period_end_is_denied(self, entity):
        _make_subscription(
            entity, _make_plan(), status="past_due",
            current_period_end=timezone.now() - timedelta(days=1),
        )
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_past_due_with_null_period_end_is_denied(self, entity):
        _make_subscription(entity, _make_plan(), status="past_due", current_period_end=None)
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_canceled_is_denied(self, entity):
        _make_subscription(
            entity, _make_plan(), status="canceled",
            current_period_end=timezone.now() + timedelta(days=5),
        )
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_no_subscription_row_is_denied(self, entity):
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

    def test_active_subscription_without_the_feature_is_denied(self, entity):
        _make_subscription(entity, _make_plan(feature_key="some_other_feature"), status="active")
        assert is_feature_enabled(entity_id=entity.EntityId, feature_key=FEATURE_KEY) is False

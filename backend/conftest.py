"""
Project-wide pytest fixtures for the SusDevOS backend test suite.

DJANGO_SETTINGS_MODULE is configured in pyproject.toml ([tool.pytest]).

Fixture hierarchy:
    gwp_dataset       — IPCC AR6 GWP100 dataset (required by emissions tests)
    entity            — a seeded Entities row
    admin_user        — user with Admin role bound to the entity
    superadmin_user   — IsSuperAdmin=True, no entity
    api_client        — unauthenticated DRF APIClient
    auth_client       — APIClient pre-authenticated as admin_user
    sa_client         — APIClient pre-authenticated as superadmin_user
"""
from rest_framework.test import APIClient

import pytest

# ── GWP dataset ───────────────────────────────────────────────────────────────

@pytest.fixture
def gwp_dataset(db):
    """IPCC AR6 GWP100 — required by any test that creates EmissionsData."""
    from apps.emissions.models import GwpDatasets, GwpValues

    ds, _ = GwpDatasets.objects.get_or_create(
        Version="AR6", Horizon=100,
        defaults={"Name": "IPCC AR6 GWP100", "IsDefault": True, "PublishedYear": 2021},
    )
    defaults = [
        ("CO2", None, "1.0000"),
        ("CH4", "fossil", "29.8000"),
        ("N2O", None, "273.0000"),
    ]
    for gas, subtype, factor in defaults:
        GwpValues.objects.get_or_create(
            GwpDatasetId=ds, Gas=gas, GasSubtype=subtype,
            defaults={"GwpFactor": factor},
        )
    return ds


# ── Entity + users ────────────────────────────────────────────────────────────

@pytest.fixture
def entity(db):
    from apps.entities.tests.factories import EntitiesFactory
    return EntitiesFactory(EntityName="Test Corp Ltd")


@pytest.fixture
def admin_user(db, entity):
    from apps.users.tests.factories import UsersFactory

    role, _ = __import__("apps.users.models", fromlist=["Roles"]).Roles.objects.get_or_create(
        RoleKey="admin", defaults={"RoleName": "Admin"}
    )
    user = UsersFactory(EntityId=entity, email="admin@testcorp.com", username="testadmin")
    from apps.users.models import UserRoles
    UserRoles.objects.create(UserId=user, RoleId=role)
    return user


@pytest.fixture
def superadmin_user(db):
    from apps.users.tests.factories import SuperAdminFactory
    return SuperAdminFactory(email="sa@susdevos.com", username="testsa")


# ── API clients ───────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


def _get_token(user):
    """Issue a real JWT access token for the given user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    return str(RefreshToken.for_user(user).access_token)


@pytest.fixture
def auth_client(admin_user, entity):
    """APIClient authenticated as admin_user with X-Entity-ID set."""
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {_get_token(admin_user)}",
        HTTP_X_ENTITY_ID=str(entity.EntityId),
    )
    return client


@pytest.fixture
def sa_client(superadmin_user):
    """APIClient authenticated as SuperAdmin (no entity context by default)."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {_get_token(superadmin_user)}")
    return client


@pytest.fixture
def entity_id():
    """The default tenant id used by data-layer factories."""
    return 1


# ── Feature gates ─────────────────────────────────────────────────────────────

@pytest.fixture
def enable_feature(db):
    """Grant a gated feature to an entity via an active test subscription.

    Server-side feature gates (FeatureGateMixin) deny any entity without an
    active subscription that includes the feature, so tests exercising a gated
    endpoint must grant the feature first.  Calling more than once accumulates
    features onto the same shared plan, so an entity can hold several at once.
    """
    def _grant(entity, feature_key):
        from apps.billing.models import EntitySubscriptions, PlanFeatures, Plans

        plan, _ = Plans.objects.get_or_create(
            PlanKey="test_feature_plan",
            defaults={
                "PlanName": "Test Feature Plan",
                "PriceMonthlyGBP": 0,
                "PriceAnnualGBP": 0,
                "MaxEntities": 0,
                "MaxUsersPerEntity": 0,
                "MaxReportingYears": 0,
                "SupportTier": "standard",
            },
        )
        PlanFeatures.objects.get_or_create(
            PlanId=plan,
            FeatureKey=feature_key,
            defaults={"IsEnabled": True, "UpgradeMessage": "Upgrade to use this feature."},
        )
        EntitySubscriptions.objects.get_or_create(
            EntityId=entity,
            defaults={"PlanId": plan, "Status": "active"},
        )
    return _grant

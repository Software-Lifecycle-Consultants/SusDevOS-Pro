"""
GHG Inventory lifecycle tests.

Covers the full workflow for GHGInventories:
  - POST  /api/ghg-inventories/          (create)
  - PATCH /api/ghg-inventories/{id}/     (edit while unverified — allowed)
  - PATCH VerificationStatus=3           (verify)
  - PATCH after verification → 403 verified_immutable
  - DELETE after verification → 403 verified_immutable
  - POST  /api/ghg-inventories/{id}/unlock/ (SuperAdmin only, reason required)
  - Feature gate: entity without plan → HTTP 402 feature_gated

The inventory API uses FeatureGateMixin (required_feature="ghg_inventory_formal"),
so tests that use auth_client must have the feature enabled on the entity's plan.
SuperAdmin (sa_client) bypasses the gate automatically.
"""

from rest_framework import status
from rest_framework.test import APIClient

import pytest

INV_URL = "/api/ghg-inventories/"
VERIFIED = 3  # VerificationStatus >= VERIFIED → immutable

pytestmark = pytest.mark.django_db


# ── Helpers ──────────────────────────────────────────────────────────────────


def _enable_inventory_feature(entity):
    """Seed a plan + subscription that includes 'ghg_inventory_formal'."""
    from apps.billing.models import EntitySubscriptions, PlanFeatures, Plans

    plan, _ = Plans.objects.get_or_create(
        PlanKey="pro_inventory_test",
        defaults={
            "PlanName": "Pro (test)",
            "PriceMonthlyGBP": 99,
            "PriceAnnualGBP": 990,
            "MaxEntities": 0,
            "MaxUsersPerEntity": 0,
            "MaxReportingYears": 0,
            "SupportTier": "standard",
        },
    )
    PlanFeatures.objects.get_or_create(
        PlanId=plan,
        FeatureKey="ghg_inventory_formal",
        defaults={"IsEnabled": True, "UpgradeMessage": "Upgrade to use formal inventories."},
    )
    EntitySubscriptions.objects.get_or_create(
        EntityId=entity,
        defaults={"PlanId": plan, "Status": "active"},
    )


def _inv_payload(gwp_id):
    return {
        "ReportingYear": 2024,
        "ReportingPeriodFrom": "2024-01-01",
        "ReportingPeriodTo": "2024-12-31",
        "BaselineYear": 2019,
        "GwpDatasetId": gwp_id,
        "ConsolidationApproach": 2,  # Financial Control
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def activate_feature(entity):
    """Enable ghg_inventory_formal on the shared test entity before each test."""
    _enable_inventory_feature(entity)


# ── CRUD ──────────────────────────────────────────────────────────────────────


class TestInventoryCreate:
    def test_create_returns_201(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_create_sets_correct_entity(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.data["EntityId"] == entity.EntityId

    def test_create_defaults_to_unverified(self, auth_client, gwp_dataset):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.data["VerificationStatus"] == 1  # Unverified

    def test_unauthenticated_returns_401(self, api_client, gwp_dataset):
        resp = api_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestInventoryEdit:
    def test_can_edit_unverified_inventory(self, auth_client, gwp_dataset):
        inv_id = auth_client.post(
            INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json"
        ).data["InventoryId"]

        patch = auth_client.patch(f"{INV_URL}{inv_id}/", {"BaselineYear": 2020}, format="json")
        assert patch.status_code == status.HTTP_200_OK
        assert patch.data["BaselineYear"] == 2020


# ── Verification workflow ──────────────────────────────────────────────────────


class TestInventoryVerification:
    def _create(self, auth_client, gwp_dataset):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.data["InventoryId"]

    def _verify(self, auth_client, inv_id):
        """Advance to Verified by patching VerificationStatus directly."""
        resp = auth_client.patch(
            f"{INV_URL}{inv_id}/", {"VerificationStatus": VERIFIED}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["VerificationStatus"] == VERIFIED

    def test_patch_verified_inventory_returns_403(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)
        self._verify(auth_client, inv_id)

        patch = auth_client.patch(f"{INV_URL}{inv_id}/", {"BaselineYear": 2021}, format="json")
        assert patch.status_code == status.HTTP_403_FORBIDDEN
        assert patch.data["code"] == "verified_immutable"

    def test_delete_verified_inventory_returns_403(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)
        self._verify(auth_client, inv_id)

        resp = auth_client.delete(f"{INV_URL}{inv_id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_unverified_inventory_can_be_deleted(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)
        resp = auth_client.delete(f"{INV_URL}{inv_id}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT


# ── Unlock (SuperAdmin only) ───────────────────────────────────────────────────


class TestInventoryUnlock:
    def _create_and_verify(self, auth_client, gwp_dataset):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        inv_id = resp.data["InventoryId"]
        auth_client.patch(f"{INV_URL}{inv_id}/", {"VerificationStatus": VERIFIED}, format="json")
        return inv_id

    def test_non_sa_cannot_unlock(self, auth_client, gwp_dataset):
        inv_id = self._create_and_verify(auth_client, gwp_dataset)
        resp = auth_client.post(f"{INV_URL}{inv_id}/unlock/", {"reason": "Oops"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_sa_can_unlock_with_reason(self, auth_client, sa_client, gwp_dataset, entity):
        inv_id = self._create_and_verify(auth_client, gwp_dataset)

        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        unlock = sa_client.post(
            f"{INV_URL}{inv_id}/unlock/",
            {"reason": "Error in baseline data — correcting per client request"},
            format="json",
        )
        assert unlock.status_code == status.HTTP_204_NO_CONTENT

        # Must be back to Unverified (1)
        detail = auth_client.get(f"{INV_URL}{inv_id}/")
        assert detail.data["VerificationStatus"] == 1

    def test_sa_unlock_without_reason_returns_400(
        self, auth_client, sa_client, gwp_dataset, entity
    ):
        inv_id = self._create_and_verify(auth_client, gwp_dataset)

        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        resp = sa_client.post(f"{INV_URL}{inv_id}/unlock/", {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["code"] == "reason_required"

    def test_sa_unlock_restores_editability(self, auth_client, sa_client, gwp_dataset, entity):
        """After unlocking, the admin can edit the inventory again."""
        inv_id = self._create_and_verify(auth_client, gwp_dataset)

        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        sa_client.post(
            f"{INV_URL}{inv_id}/unlock/",
            {"reason": "Correcting baseline"},
            format="json",
        )

        patch = auth_client.patch(f"{INV_URL}{inv_id}/", {"BaselineYear": 2021}, format="json")
        assert patch.status_code == status.HTTP_200_OK


# ── Feature gate ──────────────────────────────────────────────────────────────


class TestInventoryFeatureGate:
    def test_entity_without_plan_gets_402(self, gwp_dataset):
        """
        An entity that has no active subscription with 'ghg_inventory_formal'
        must receive HTTP 402 with code='feature_gated', not a silent pass.
        """
        from rest_framework_simplejwt.tokens import RefreshToken

        from apps.entities.tests.factories import EntitiesFactory
        from apps.users.tests.factories import UsersFactory

        ungated_entity = EntitiesFactory(EntityName="Free Tier Corp")
        user = UsersFactory(
            EntityId=ungated_entity, email="free@freetier.com", username="free_user"
        )
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
            HTTP_X_ENTITY_ID=str(ungated_entity.EntityId),
        )

        resp = client.get(INV_URL)
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED
        assert resp.data.get("code") == "feature_gated"
        assert resp.data.get("feature") == "ghg_inventory_formal"
        assert "upgrade_url" in resp.data

    def test_superadmin_bypasses_feature_gate(self, sa_client, gwp_dataset):
        """SuperAdmin can always access the inventory API regardless of plan."""
        resp = sa_client.get(INV_URL)
        assert resp.status_code == status.HTTP_200_OK

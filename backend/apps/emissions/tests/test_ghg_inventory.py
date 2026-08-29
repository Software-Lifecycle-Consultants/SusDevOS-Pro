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

from decimal import Decimal

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.emissions.models import EmissionsData
from apps.shared.models import AuditLog

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

    def test_first_party_contract_round_trips_boundary_and_baseline(
        self, auth_client, gwp_dataset
    ):
        payload = _inv_payload(gwp_dataset.GwpDatasetId)
        payload["BoundaryNotes"] = "UK operations included; leased assets excluded."

        created = auth_client.post(INV_URL, payload, format="json")
        assert created.status_code == status.HTTP_201_CREATED, created.data
        detail = auth_client.get(f"{INV_URL}{created.data['InventoryId']}/")

        assert detail.data["ReportingPeriodFrom"] == "2024-01-01"
        assert detail.data["ReportingPeriodTo"] == "2024-12-31"
        assert detail.data["BaselineYear"] == 2019
        assert detail.data["BoundaryNotes"] == payload["BoundaryNotes"]
        assert detail.data["GwpDatasetId"] == gwp_dataset.GwpDatasetId
        assert detail.data["GwpDatasetName"] == gwp_dataset.Name

    def test_active_default_gwp_dataset_is_recorded_when_omitted(
        self, auth_client, gwp_dataset
    ):
        payload = _inv_payload(gwp_dataset.GwpDatasetId)
        payload.pop("GwpDatasetId")

        response = auth_client.post(INV_URL, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["GwpDatasetId"] == gwp_dataset.GwpDatasetId
        assert response.data["GwpDatasetName"] == gwp_dataset.Name

    def test_unknown_legacy_base_year_key_is_rejected(self, auth_client, gwp_dataset):
        payload = _inv_payload(gwp_dataset.GwpDatasetId)
        payload["BaseYear"] = payload.pop("BaselineYear")

        response = auth_client.post(INV_URL, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "BaseYear" in response.data["errors"]

    @pytest.mark.parametrize(
        "changes,error_field",
        [
            (
                {"ReportingPeriodFrom": "2024-12-31", "ReportingPeriodTo": "2024-01-01"},
                "ReportingPeriodTo",
            ),
            (
                {"ReportingPeriodFrom": "2023-01-01", "ReportingPeriodTo": "2024-12-31"},
                "ReportingPeriodTo",
            ),
            ({"ReportingYear": 2023}, "ReportingYear"),
            ({"BaselineYear": 2025}, "BaselineYear"),
        ],
    )
    def test_invalid_inventory_boundary_is_rejected(
        self, changes, error_field, auth_client, gwp_dataset
    ):
        payload = _inv_payload(gwp_dataset.GwpDatasetId)
        payload.update(changes)

        response = auth_client.post(INV_URL, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_field in response.data["errors"]


class TestInventoryEdit:
    def test_can_edit_unverified_inventory(self, auth_client, gwp_dataset):
        inv_id = auth_client.post(
            INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json"
        ).data["InventoryId"]

        patch = auth_client.patch(f"{INV_URL}{inv_id}/", {"BaselineYear": 2020}, format="json")
        assert patch.status_code == status.HTTP_200_OK
        assert patch.data["BaselineYear"] == 2020

    @pytest.mark.parametrize(
        "field,value",
        [
            ("VerificationStatus", 3),
            ("TotalScope1Tonnes", "999.000000"),
            ("TotalsLastComputedAt", "2026-08-25T12:00:00Z"),
        ],
    )
    def test_server_managed_fields_are_rejected(
        self, field, value, auth_client, gwp_dataset
    ):
        inv_id = auth_client.post(
            INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json"
        ).data["InventoryId"]

        response = auth_client.patch(
            f"{INV_URL}{inv_id}/", {field: value}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field in response.data["errors"]

    def test_boundary_cannot_change_after_records_are_assigned(
        self, auth_client, entity, gwp_dataset
    ):
        inv_id = auth_client.post(
            INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json"
        ).data["InventoryId"]
        from apps.emissions.models import GHGInventories

        inventory = GHGInventories.objects.get(InventoryId=inv_id)
        EmissionsData.objects.create(
            EntityId=entity,
            InventoryId=inventory,
            Title="Assigned fuel",
            Scope=1,
            QuantityOrCost=Decimal("10.0000"),
            Unit="litres",
            EmissionFactor=Decimal("2.63900000"),
            EmissionFactorSource="Test factor",
            Gas="CO2",
            GwpDatasetId=gwp_dataset,
            ReportingYear=2024,
            ReportingPeriodFrom="2024-01-01",
            ReportingPeriodTo="2024-01-31",
        )

        response = auth_client.patch(
            f"{INV_URL}{inv_id}/",
            {"ReportingPeriodFrom": "2024-02-01"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ReportingPeriodFrom" in response.data["errors"]

    def test_unassigned_reconciliation_lists_candidates_and_incomplete_records(
        self, auth_client, entity, gwp_dataset
    ):
        inv_id = auth_client.post(
            INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json"
        ).data["InventoryId"]
        common = {
            "EntityId": entity,
            "Scope": 1,
            "QuantityOrCost": Decimal("1.0000"),
            "Unit": "litres",
            "EmissionFactor": Decimal("2.63900000"),
            "EmissionFactorSource": "Test factor",
            "Gas": "CO2",
            "GwpDatasetId": gwp_dataset,
            "ReportingYear": 2024,
        }
        candidate = EmissionsData.objects.create(
            **common,
            Title="Candidate",
            ReportingPeriodFrom="2024-02-01",
            ReportingPeriodTo="2024-02-29",
        )
        incomplete = EmissionsData.objects.create(**common, Title="Needs dates")
        EmissionsData.objects.create(
            **{**common, "ReportingYear": 2023},
            Title="Different year",
        )

        response = auth_client.get(
            f"{INV_URL}{inv_id}/unassigned-emissions/"
        )

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["candidate_count"] == 1
        assert response.data["incomplete_count"] == 1
        assert response.data["candidates"][0]["EmissionsId"] == candidate.EmissionsId
        assert response.data["incomplete"][0]["EmissionsId"] == incomplete.EmissionsId


# ── Verification workflow ──────────────────────────────────────────────────────


class TestInventoryVerification:
    def _create(self, auth_client, gwp_dataset):
        resp = auth_client.post(INV_URL, _inv_payload(gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.data["InventoryId"]

    def _verify(self, auth_client, inv_id):
        submitted = auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        assert submitted.status_code == status.HTTP_200_OK, submitted.data
        resp = auth_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["VerificationStatus"] == VERIFIED

    def test_direct_status_patch_is_rejected(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)

        response = auth_client.patch(
            f"{INV_URL}{inv_id}/", {"VerificationStatus": VERIFIED}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "VerificationStatus" in response.data["errors"]

    def test_submit_moves_unverified_inventory_to_pending(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)

        response = auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["VerificationStatus"] == 2

    def test_verify_requires_pending_state(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)

        response = auth_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "invalid_transition"

    @staticmethod
    def _client_for(entity, *, role_key, email, username):
        """Authenticated client for a user holding exactly one role."""
        from rest_framework_simplejwt.tokens import RefreshToken

        from apps.users.models import Roles, UserRoles
        from apps.users.tests.factories import UsersFactory

        user = UsersFactory(EntityId=entity, email=email, username=username)
        if role_key is not None:
            role, _ = Roles.objects.get_or_create(
                RoleKey=role_key, defaults={"RoleName": role_key.title()}
            )
            UserRoles.objects.create(UserId=user, RoleId=role, Status=1)
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        return client

    def test_roleless_member_cannot_verify(self, auth_client, entity, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        member_client = self._client_for(
            entity,
            role_key=None,
            email="inventory-member@testcorp.com",
            username="inventory_member",
        )

        response = member_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_cannot_verify(self, auth_client, entity, gwp_dataset):
        """Whoever enters the figures must not be the one who signs them off."""
        inv_id = self._create(auth_client, gwp_dataset)
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        staff_client = self._client_for(
            entity,
            role_key="staff",
            email="inventory-staff@testcorp.com",
            username="inventory_staff",
        )

        response = staff_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_can_verify(self, auth_client, entity, gwp_dataset):
        """Verification is a sustainability-manager task, not an Admin one."""
        inv_id = self._create(auth_client, gwp_dataset)
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        manager_client = self._client_for(
            entity,
            role_key="manager",
            email="inventory-manager@testcorp.com",
            username="inventory_manager",
        )

        response = manager_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["VerificationStatus"] == 3

    def test_submit_requires_review_of_matching_unassigned_records(
        self, auth_client, entity, gwp_dataset
    ):
        inv_id = self._create(auth_client, gwp_dataset)
        EmissionsData.objects.create(
            EntityId=entity,
            Title="Unassigned electricity",
            Scope=2,
            QuantityOrCost=Decimal("100.0000"),
            Unit="kWh",
            EmissionFactor=Decimal("0.20000000"),
            EmissionFactorSource="Test grid factor",
            Gas="CO2",
            GwpDatasetId=gwp_dataset,
            ReportingYear=2024,
            ReportingPeriodFrom="2024-01-01",
            ReportingPeriodTo="2024-12-31",
        )

        blocked = auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        acknowledged = auth_client.post(
            f"{INV_URL}{inv_id}/submit/",
            {"acknowledge_unassigned": True},
            format="json",
        )

        assert blocked.status_code == status.HTTP_409_CONFLICT
        assert blocked.data["code"] == "unassigned_records_require_review"
        assert blocked.data["candidate_count"] == 1
        assert acknowledged.status_code == status.HTTP_200_OK, acknowledged.data
        assert acknowledged.data["VerificationStatus"] == 2

    def test_verify_is_audited(self, auth_client, gwp_dataset):
        inv_id = self._create(auth_client, gwp_dataset)
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")

        response = auth_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert AuditLog.objects.filter(
            Action="Verify",
            TableName="ghg_inventories",
            RecordId=inv_id,
        ).exists()

    def test_verify_stamps_verifier_identity(self, auth_client, admin_user, gwp_dataset):
        """Verifying an inventory must record who verified it and when."""
        inv_id = self._create(auth_client, gwp_dataset)
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        resp = auth_client.post(
            f"{INV_URL}{inv_id}/verify/", {"notes": "Reviewed source evidence"}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["VerifiedBy"] == admin_user.UserId
        assert resp.data["VerifiedAt"] is not None
        assert resp.data["VerificationNotes"] == "Reviewed source evidence"

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
        auth_client.post(f"{INV_URL}{inv_id}/submit/", {}, format="json")
        auth_client.post(f"{INV_URL}{inv_id}/verify/", {}, format="json")
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

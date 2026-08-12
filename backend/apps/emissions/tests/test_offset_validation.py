"""
Carbon offset validation tests.

Verifies the critical business rule (CLAUDE.md):
  "Unvalidated credits are never deducted from net inventory totals."

Only offsets with RegistryValidationStatus='valid' may reduce NetEmissionsTonnes.
Offsets with status 'unverified', 'pending', or 'invalid' must be ignored when
computing the net total.

Also tests the nested offset API (POST /api/emissions/{id}/offsets/) which does
NOT require a plan feature — it is accessible to all authenticated users who can
access the parent emissions record.

IMPORTANT: _compute_inventory_totals() in tasks/emissions.py had a bug where it
summed ALL offsets regardless of RegistryValidationStatus.  The test
test_only_valid_offsets_reduce_net_total documents the correct behaviour and
will fail until the bug is fixed.
"""

from decimal import Decimal

from rest_framework import status

import pytest

from apps.emissions.models import EmissionsOffsets, GHGInventories
from apps.entities.tests.factories import EntitiesFactory

pytestmark = pytest.mark.django_db

EMISSIONS_URL = "/api/emissions/"
DIESEL_EF = "2.63900000"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _post_record(client, gwp_id, year=2024):
    resp = client.post(
        EMISSIONS_URL,
        {
            "Title": "Diesel",
            "Scope": 1,
            "QuantityOrCost": "1000.0000",
            "Unit": "litres",
            "EmissionFactor": DIESEL_EF,
            "EmissionFactorSource": "DEFRA 2024",
            "Gas": "CO2",
            "GwpDatasetId": gwp_id,
            "ReportingYear": year,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    return resp.data["EmissionsId"]


def _create_inventory(entity, gwp_dataset, year=2024):
    return GHGInventories.objects.create(
        EntityId=entity,
        ReportingYear=year,
        ReportingPeriodFrom=f"{year}-01-01",
        ReportingPeriodTo=f"{year}-12-31",
        GwpDatasetId=gwp_dataset,
    )


def _add_offset(entity, emissions_record_id, amount_tonnes, validation_status):
    from apps.emissions.models import EmissionsData

    record = EmissionsData.objects.get(pk=emissions_record_id)
    return EmissionsOffsets.objects.create(
        EntityId=entity,
        EmissionsId=record,
        Title=f"Offset ({validation_status})",
        OffsetType="vcs",
        Provider="Verra",
        OffsetAmountTonnes=Decimal(str(amount_tonnes)),
        CreditRegistry="verra",
        RegistryValidationStatus=validation_status,
    )


# ── Nested offset API ─────────────────────────────────────────────────────────


class TestOffsetAPI:
    """POST /api/emissions/{id}/offsets/ — accessible without a billing feature gate."""

    def test_add_offset_to_record(self, auth_client, gwp_dataset, entity):
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        resp = auth_client.post(
            f"{EMISSIONS_URL}{eid}/offsets/",
            {
                "Title": "Kariba REDD+ VCU",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "1.500000",
                "CreditRegistry": "verra",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["RegistryValidationStatus"] == "unverified"

    def test_offset_lists_for_own_record(self, auth_client, gwp_dataset, entity):
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        auth_client.post(
            f"{EMISSIONS_URL}{eid}/offsets/",
            {
                "Title": "Credit A",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "2.000000",
                "CreditRegistry": "verra",
            },
            format="json",
        )
        resp = auth_client.get(f"{EMISSIONS_URL}{eid}/offsets/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1

    def test_offset_for_other_entity_record_returns_404(self, auth_client, gwp_dataset, entity):
        """Adding an offset to another entity's record must return 404."""
        other_entity = EntitiesFactory(EntityName="Other Corp")
        from rest_framework.test import APIClient

        from rest_framework_simplejwt.tokens import RefreshToken

        from apps.users.tests.factories import UsersFactory

        other_user = UsersFactory(
            EntityId=other_entity, email="other@corp.com", username="other_user"
        )
        other_client = APIClient()
        other_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other_user).access_token}",
            HTTP_X_ENTITY_ID=str(other_entity.EntityId),
        )
        other_eid = _post_record(other_client, gwp_dataset.GwpDatasetId)

        # auth_client (entity A) tries to add an offset to entity B's record
        resp = auth_client.post(
            f"{EMISSIONS_URL}{other_eid}/offsets/",
            {
                "Title": "Infiltrated offset",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "1.0",
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


# ── Net total validation rule ─────────────────────────────────────────────────


class TestOffsetNetTotalRule:
    """
    Critical rule: only 'valid' offsets reduce NetEmissionsTonnes.
    'unverified', 'pending', and 'invalid' credits must be excluded.
    """

    def test_only_valid_offsets_reduce_net_total(self, auth_client, gwp_dataset, entity):
        """
        Given:
          - 1 emissions record (2.639 tCO2e from 1000 L diesel)
          - 1 offset with status='unverified' (1.0 tCO2e)
          - 1 offset with status='invalid'    (1.0 tCO2e)
          - 1 offset with status='pending'    (1.0 tCO2e)
          - 1 offset with status='valid'      (1.0 tCO2e)

        Expected net = gross_emissions - only_valid_offset
                     = 2.639 - 1.0 = 1.639 tCO2e (approximately)
        The other 3 × 1.0 tCO2e of unvalidated credits must NOT be subtracted.
        """
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        inventory = _create_inventory(entity, gwp_dataset)

        for vs in ("unverified", "invalid", "pending"):
            _add_offset(entity, eid, "1.000000", vs)
        _add_offset(entity, eid, "1.000000", "valid")

        # Run the inventory total computation directly (Celery task helper)
        from tasks.emissions import _compute_inventory_totals

        _compute_inventory_totals(inventory)
        inventory.refresh_from_db()

        gross = inventory.TotalScope1Tonnes
        assert gross is not None and gross > 0

        # Only the 1 'valid' credit (1.0 tCO2e) should be deducted
        assert inventory.TotalOffsetsTonnes == Decimal("1.000000")
        expected_net = gross - Decimal("1.000000")
        assert inventory.NetEmissionsTonnes == expected_net

    def test_all_invalid_offsets_result_in_zero_deduction(self, auth_client, gwp_dataset, entity):
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        inventory = _create_inventory(entity, gwp_dataset)

        for vs in ("unverified", "invalid", "pending"):
            _add_offset(entity, eid, "5.000000", vs)

        from tasks.emissions import _compute_inventory_totals

        _compute_inventory_totals(inventory)
        inventory.refresh_from_db()

        # No valid offsets → deduction is zero
        assert inventory.TotalOffsetsTonnes == Decimal("0.000000")
        assert inventory.NetEmissionsTonnes == inventory.TotalScope1Tonnes

    def test_valid_offset_is_fully_deducted(self, auth_client, gwp_dataset, entity):
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        inventory = _create_inventory(entity, gwp_dataset)

        _add_offset(entity, eid, "1.000000", "valid")

        from tasks.emissions import _compute_inventory_totals

        _compute_inventory_totals(inventory)
        inventory.refresh_from_db()

        assert inventory.TotalOffsetsTonnes == Decimal("1.000000")
        assert inventory.NetEmissionsTonnes == inventory.TotalScope1Tonnes - Decimal("1.000000")

    def test_multiple_valid_offsets_all_deducted(self, auth_client, gwp_dataset, entity):
        eid = _post_record(auth_client, gwp_dataset.GwpDatasetId)
        inventory = _create_inventory(entity, gwp_dataset)

        for _ in range(3):
            _add_offset(entity, eid, "0.500000", "valid")

        from tasks.emissions import _compute_inventory_totals

        _compute_inventory_totals(inventory)
        inventory.refresh_from_db()

        assert inventory.TotalOffsetsTonnes == Decimal("1.500000")
        expected_net = inventory.TotalScope1Tonnes - Decimal("1.500000")
        assert inventory.NetEmissionsTonnes == expected_net

    def test_valid_offset_in_other_year_does_not_reduce_this_years_net(
        self, auth_client, gwp_dataset, entity
    ):
        """
        A valid offset attached to a 2023 emissions record must NOT reduce the
        2024 inventory's net total.  Offsets are scoped to the inventory's
        ReportingYear via their linked emissions record, so credits cannot leak
        across years.  Regression test for the entity-wide offset sum bug.
        """
        # 2024 inventory with a 2024 record but no 2024 offsets.
        _post_record(auth_client, gwp_dataset.GwpDatasetId, year=2024)
        inv_2024 = _create_inventory(entity, gwp_dataset, year=2024)

        # A valid credit, but attached to a 2023 record.
        eid_2023 = _post_record(auth_client, gwp_dataset.GwpDatasetId, year=2023)
        _add_offset(entity, eid_2023, "1.000000", "valid")

        from tasks.emissions import _compute_inventory_totals

        _compute_inventory_totals(inv_2024)
        inv_2024.refresh_from_db()

        # The 2023 credit must not touch 2024's totals.
        assert inv_2024.TotalOffsetsTonnes == Decimal("0.000000")
        assert inv_2024.NetEmissionsTonnes == inv_2024.TotalScope1Tonnes


# ── Verified-record immutability on the standalone offsets endpoint ────────────


def _enable_offsets_feature(entity):
    """Seed a plan + subscription that includes 'carbon_offsets' so the
    standalone /api/emissions-offsets/ endpoint is reachable (FeatureGateMixin)."""
    from apps.billing.models import EntitySubscriptions, PlanFeatures, Plans

    plan, _ = Plans.objects.get_or_create(
        PlanKey="offsets_test",
        defaults={
            "PlanName": "Offsets (test)",
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
        FeatureKey="carbon_offsets",
        defaults={"IsEnabled": True, "UpgradeMessage": "Upgrade to manage offsets."},
    )
    EntitySubscriptions.objects.get_or_create(
        EntityId=entity,
        defaults={"PlanId": plan, "Status": "active"},
    )


class TestStandaloneOffsetVerifiedLock:
    """The standalone offsets endpoint (/api/emissions-offsets/{id}/) must honour
    the verified-record immutability lock (CLAUDE.md rule #3), exactly like the
    nested /api/emissions/{id}/offsets/{id}/ action.  Without this an offset on a
    verified (audit-locked) record could be silently edited or deleted, changing
    the recomputed net-emissions figure without the SuperAdmin unlock path."""

    OFFSETS_URL = "/api/emissions-offsets/"

    def _make_offset_on_verified_record(self, auth_client, gwp_id):
        eid = _post_record(auth_client, gwp_id)
        created = auth_client.post(
            f"{EMISSIONS_URL}{eid}/offsets/",
            {
                "Title": "Credit A",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "2.000000",
                "CreditRegistry": "verra",
            },
            format="json",
        )
        assert created.status_code == status.HTTP_201_CREATED, created.data
        offset_id = created.data["OffsetId"]
        # Verify (locks) the parent record.
        verify = auth_client.post(f"{EMISSIONS_URL}{eid}/verify/", {"notes": "ok"}, format="json")
        assert verify.status_code == status.HTTP_204_NO_CONTENT
        return offset_id

    def test_patch_offset_on_verified_record_is_forbidden(self, auth_client, gwp_dataset, entity):
        _enable_offsets_feature(entity)
        offset_id = self._make_offset_on_verified_record(auth_client, gwp_dataset.GwpDatasetId)

        resp = auth_client.patch(
            f"{self.OFFSETS_URL}{offset_id}/",
            {"OffsetAmountTonnes": "999.000000"},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN, resp.data
        assert resp.data["code"] == "verified_immutable"

        offset = EmissionsOffsets.objects.get(OffsetId=offset_id)
        assert offset.OffsetAmountTonnes == Decimal("2.000000")  # unchanged

    def test_delete_offset_on_verified_record_is_forbidden(self, auth_client, gwp_dataset, entity):
        _enable_offsets_feature(entity)
        offset_id = self._make_offset_on_verified_record(auth_client, gwp_dataset.GwpDatasetId)

        resp = auth_client.delete(f"{self.OFFSETS_URL}{offset_id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN, resp.data

        offset = EmissionsOffsets.objects.get(OffsetId=offset_id)
        assert offset.Status != 4  # not soft-deleted

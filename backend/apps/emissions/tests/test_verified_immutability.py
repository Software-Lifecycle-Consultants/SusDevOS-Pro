"""
Regression tests for verified-record / verified-inventory immutability
(CLAUDE.md rule #3: "Verified inventories are immutable. VerificationStatus >= 3
→ reject edits with HTTP 403").

These cover gaps found in the critical-rules audit:

  F1 — The standalone EmissionsOffsetsViewSet (/api/emissions-offsets/) must
       reject PATCH/DELETE of an offset attached to a verified emissions record,
       matching the guard the nested offset actions already enforce. Otherwise
       it is a bypass that mutates an audit-locked net-emissions input.

  F2 — EmissionsData rows belonging to a verified GHG inventory must reject
       edit and delete. A verified inventory's totals are frozen (the nightly
       recompute skips verified inventories), so mutating the underlying rows
       silently diverges the locked totals from the data.

  F3 — New EmissionsData rows cannot be added to a verified GHG inventory.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

EMISSIONS_URL = "/api/emissions/"
OFFSETS_URL = "/api/emissions-offsets/"
INV_URL = "/api/ghg-inventories/"
VERIFIED = 3
DIESEL_EF = "2.63900000"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _enable_feature(entity, feature_key):
    """Add ``feature_key`` to a shared test plan the entity is subscribed to.

    Called more than once accumulates features onto the same plan, so an entity
    can hold several gated features at once (e.g. carbon_offsets AND
    ghg_inventory_formal)."""
    from apps.billing.models import EntitySubscriptions, PlanFeatures, Plans

    plan, _ = Plans.objects.get_or_create(
        PlanKey="immutability_test_plan",
        defaults={
            "PlanName": "Immutability Test Plan",
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


def _post_record(client, gwp_id, inventory_id=None, year=2024):
    payload = {
        "Title": "Diesel",
        "Scope": 1,
        "QuantityOrCost": "1000.0000",
        "Unit": "litres",
        "EmissionFactor": DIESEL_EF,
        "EmissionFactorSource": "DEFRA 2024",
        "Gas": "CO2",
        "GwpDatasetId": gwp_id,
        "ReportingYear": year,
    }
    if inventory_id is not None:
        payload["InventoryId"] = inventory_id
    return client.post(EMISSIONS_URL, payload, format="json")


def _create_inventory(entity, gwp_dataset, year=2024):
    from apps.emissions.models import GHGInventories

    return GHGInventories.objects.create(
        EntityId=entity,
        ReportingYear=year,
        ReportingPeriodFrom=f"{year}-01-01",
        ReportingPeriodTo=f"{year}-12-31",
        GwpDatasetId=gwp_dataset,
    )


# ── F1: standalone offsets viewset honours the parent record's verified lock ──


class TestStandaloneOffsetVerifiedLock:
    def _make_offset_on_verified_record(self, auth_client, gwp_dataset):
        rec_id = _post_record(auth_client, gwp_dataset.GwpDatasetId).data["EmissionsId"]

        # Add an offset via the nested route while the record is still editable.
        offset_resp = auth_client.post(
            f"{EMISSIONS_URL}{rec_id}/offsets/",
            {
                "Title": "VCS offset",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "10.000000",
                "CreditRegistry": "verra",
            },
            format="json",
        )
        assert offset_resp.status_code == status.HTTP_201_CREATED, offset_resp.data
        offset_id = offset_resp.data["OffsetId"]

        # Verify the parent record → it (and its offsets) become immutable.
        verify = auth_client.post(f"{EMISSIONS_URL}{rec_id}/verify/")
        assert verify.status_code == status.HTTP_204_NO_CONTENT
        return offset_id

    def test_patch_offset_of_verified_record_returns_403(self, auth_client, gwp_dataset, entity):
        _enable_feature(entity, "carbon_offsets")
        offset_id = self._make_offset_on_verified_record(auth_client, gwp_dataset)

        resp = auth_client.patch(
            f"{OFFSETS_URL}{offset_id}/", {"OffsetAmountTonnes": "999.000000"}, format="json"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_delete_offset_of_verified_record_returns_403(self, auth_client, gwp_dataset, entity):
        _enable_feature(entity, "carbon_offsets")
        offset_id = self._make_offset_on_verified_record(auth_client, gwp_dataset)

        resp = auth_client.delete(f"{OFFSETS_URL}{offset_id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_patch_offset_of_unverified_record_is_allowed(self, auth_client, gwp_dataset, entity):
        """The lock must not fire for offsets on an unverified record."""
        _enable_feature(entity, "carbon_offsets")
        rec_id = _post_record(auth_client, gwp_dataset.GwpDatasetId).data["EmissionsId"]
        offset_resp = auth_client.post(
            f"{EMISSIONS_URL}{rec_id}/offsets/",
            {
                "Title": "VCS offset",
                "OffsetType": "vcs",
                "Provider": "Verra",
                "OffsetAmountTonnes": "10.000000",
                "CreditRegistry": "verra",
            },
            format="json",
        )
        offset_id = offset_resp.data["OffsetId"]

        resp = auth_client.patch(
            f"{OFFSETS_URL}{offset_id}/", {"OffsetAmountTonnes": "12.000000"}, format="json"
        )
        assert resp.status_code == status.HTTP_200_OK


# ── F2 / F3: rows under a verified GHG inventory are immutable ─────────────────


class TestVerifiedInventoryChildRows:
    def _verified_inventory(self, auth_client, entity, gwp_dataset):
        _enable_feature(entity, "ghg_inventory_formal")
        inv = _create_inventory(entity, gwp_dataset)
        patch = auth_client.patch(
            f"{INV_URL}{inv.InventoryId}/", {"VerificationStatus": VERIFIED}, format="json"
        )
        assert patch.status_code == status.HTTP_200_OK, patch.data
        return inv

    def test_edit_row_in_verified_inventory_returns_403(self, auth_client, gwp_dataset, entity):
        # Create the row while the inventory is still unverified.
        _enable_feature(entity, "ghg_inventory_formal")
        inv = _create_inventory(entity, gwp_dataset)
        rec_id = _post_record(
            auth_client, gwp_dataset.GwpDatasetId, inventory_id=inv.InventoryId
        ).data["EmissionsId"]

        auth_client.patch(
            f"{INV_URL}{inv.InventoryId}/", {"VerificationStatus": VERIFIED}, format="json"
        )

        resp = auth_client.patch(f"{EMISSIONS_URL}{rec_id}/", {"Title": "Tampered"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_delete_row_in_verified_inventory_returns_403(self, auth_client, gwp_dataset, entity):
        _enable_feature(entity, "ghg_inventory_formal")
        inv = _create_inventory(entity, gwp_dataset)
        rec_id = _post_record(
            auth_client, gwp_dataset.GwpDatasetId, inventory_id=inv.InventoryId
        ).data["EmissionsId"]

        auth_client.patch(
            f"{INV_URL}{inv.InventoryId}/", {"VerificationStatus": VERIFIED}, format="json"
        )

        resp = auth_client.delete(f"{EMISSIONS_URL}{rec_id}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_add_row_to_verified_inventory_returns_403(self, auth_client, gwp_dataset, entity):
        inv = self._verified_inventory(auth_client, entity, gwp_dataset)

        resp = _post_record(auth_client, gwp_dataset.GwpDatasetId, inventory_id=inv.InventoryId)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["code"] == "verified_immutable"

    def test_add_row_to_unverified_inventory_is_allowed(self, auth_client, gwp_dataset, entity):
        """The parent-inventory lock must not fire for unverified inventories."""
        _enable_feature(entity, "ghg_inventory_formal")
        inv = _create_inventory(entity, gwp_dataset)

        resp = _post_record(auth_client, gwp_dataset.GwpDatasetId, inventory_id=inv.InventoryId)
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

    def test_row_without_inventory_is_unaffected(self, auth_client, gwp_dataset, entity):
        """A standalone record (no InventoryId) still edits/deletes normally."""
        rec_id = _post_record(auth_client, gwp_dataset.GwpDatasetId).data["EmissionsId"]

        patch = auth_client.patch(f"{EMISSIONS_URL}{rec_id}/", {"Title": "Fine"}, format="json")
        assert patch.status_code == status.HTTP_200_OK

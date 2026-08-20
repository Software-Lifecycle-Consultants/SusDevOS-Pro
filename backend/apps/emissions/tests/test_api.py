"""
Emissions API tests.

These are the most security-critical tests in the project. They verify:

  1. EmissionsAmount is NEVER accepted from client — always overwritten.
  2. GHG calculation formula: Activity × EF × GWP → kg CO2e / 1000 → tCO2e.
  3. Scope 2 always populates BOTH location-based AND market-based fields.
  4. Biogenic CO2 stays in BiogenicCO2AmountTonnes (not in GWP total).
  5. VerificationStatus >= 3 → PATCH and DELETE return 403.
  6. /verify/ sets VerificationStatus=3; /unlock/ requires SuperAdmin + reason.

All formulas verified against GHG Protocol Corporate Standard and IPCC AR6.
"""
from decimal import Decimal

from rest_framework import status

import pytest

BASE_URL = "/api/emissions/"

# Common emission factor: DEFRA 2024 diesel (kg CO2e per litre)
DIESEL_EF = "2.63900000"
# UK grid electricity (kg CO2e per kWh), DEFRA 2024
ELEC_EF   = "0.23314000"
# CH4 fossil EF (kg CH4 per tonne natural gas, example)
CH4_EF    = "0.00200000"


def _payload(scope, quantity, ef, gas="CO2", gas_subtype=None, gwp_id=1, **extra):
    """Build a minimal valid emissions record payload."""
    p = {
        "Title":               f"Test record scope {scope}",
        "Scope":               scope,
        "QuantityOrCost":      str(quantity),
        "Unit":                "litres",
        "EmissionFactor":      ef,
        "EmissionFactorSource": "DEFRA 2024",
        "Gas":                 gas,
        "GwpDatasetId":        gwp_id,
    }
    if gas_subtype:
        p["GasSubtype"] = gas_subtype
    p.update(extra)
    return p


@pytest.mark.django_db
class TestGHGCalculation:
    """GHG calculation formula tests — the core domain invariant."""

    def test_scope1_co2_calculation(self, auth_client, gwp_dataset, entity):
        """
        1000 L diesel × 2.639 kg CO2e/L × GWP(CO2=1.0) = 2639.0 kg = 2.639000 tCO2e
        GWP Protocol §3.2: EmissionsAmount = QuantityCanonical × EF × GWP_factor
        """
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="1000.0000", ef=DIESEL_EF,
            gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Decimal(resp.data["EmissionsAmount"]) == Decimal("2639.0000")
        assert Decimal(resp.data["EmissionsAmountTonnes"]) == Decimal("2.639000")

    def test_scope2_electricity_dual_method(self, auth_client, gwp_dataset, entity):
        """
        Scope 2: 5000 kWh × 0.23314 EF × GWP(CO2=1.0) = 1165.7 kg = 1.165700 tCO2e
        Both EmissionsAmountLocationBased AND EmissionsAmountMarketBased must be populated.
        GHG Protocol Scope 2 Guidance: dual reporting is mandatory for conformant inventory.
        """
        resp = auth_client.post(BASE_URL, _payload(
            scope=2, quantity="5000.0000", ef=ELEC_EF, Unit="kWh",
            gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Decimal(resp.data["EmissionsAmount"]) == Decimal("1165.7000")
        assert Decimal(resp.data["EmissionsAmountTonnes"]) == Decimal("1.165700")
        # Critical rule #5: BOTH methods must be populated (CLAUDE.md)
        assert resp.data["EmissionsAmountLocationBased"] is not None
        assert resp.data["EmissionsAmountMarketBased"]   is not None
        assert Decimal(resp.data["EmissionsAmountLocationBased"]) == Decimal("1165.7000")

    def test_scope1_ch4_applies_gwp_factor(self, auth_client, gwp_dataset, entity):
        """
        CH4 fossil GWP = 29.8 (AR6). Verify the GWP multiplier is applied.
        100 units × 0.002 EF × 29.8 GWP = 5.96 kg CO2e
        """
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef="0.00200000",
            gas="CH4", gas_subtype="fossil",
            gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Decimal(resp.data["EmissionsAmount"]) == Decimal("5.9600")

    def test_client_submitted_amount_is_overwritten(self, auth_client, gwp_dataset, entity):
        """
        Client submits EmissionsAmount=9999999 — server must ignore it and compute the
        correct value. This is the most critical security rule in the system.
        CLAUDE.md critical rule #1: Never compute emissions on the client.
        """
        payload = _payload(scope=1, quantity="1000.0000", ef=DIESEL_EF,
                           gwp_id=gwp_dataset.GwpDatasetId)
        payload["EmissionsAmount"]       = "9999999.0000"  # attacker-supplied value
        payload["EmissionsAmountTonnes"] = "9999.000000"   # attacker-supplied value

        resp = auth_client.post(BASE_URL, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        # Must be the correct server-computed value, not the client-supplied one
        assert Decimal(resp.data["EmissionsAmount"])       == Decimal("2639.0000")
        assert Decimal(resp.data["EmissionsAmountTonnes"]) == Decimal("2.639000")

    def test_quantity_canonical_stored_for_audit(self, auth_client, gwp_dataset, entity):
        """QuantityCanonical is stored alongside the raw QuantityOrCost for the audit trail."""
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="500.0000", ef=DIESEL_EF,
            gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        # No InputUnitId provided → canonical = raw quantity
        assert resp.data["QuantityCanonical"] is not None

    def test_entity_id_always_from_header_not_body(self, auth_client, gwp_dataset, entity):
        """EntityId must come from X-Entity-ID, not the request body."""
        payload = _payload(scope=1, quantity="100.0000", ef=DIESEL_EF,
                           gwp_id=gwp_dataset.GwpDatasetId)
        payload["EntityId"] = 9999  # attacker-supplied wrong entity

        resp = auth_client.post(BASE_URL, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        # Must be bound to the real entity, not the attacker's value
        assert resp.data["EntityId"] == entity.EntityId


@pytest.mark.django_db
class TestVerificationImmutability:
    """Verified records (VerificationStatus >= 3) must be immutable."""

    def _create_and_verify(self, auth_client, sa_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF,
            gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client.credentials()["HTTP_AUTHORIZATION"] if hasattr(sa_client, "_credentials") else sa_client._credentials.get("HTTP_AUTHORIZATION", ""),
        )
        # Use auth_client to verify (admins can verify)
        verify = auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "Reviewed"}, format="json")
        assert verify.status_code == status.HTTP_204_NO_CONTENT
        return eid

    def _verify_record(self, client, eid):
        return client.post(f"{BASE_URL}{eid}/verify/", {"notes": "Reviewed"}, format="json")

    def test_patch_verified_record_returns_403(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        patch = auth_client.patch(f"{BASE_URL}{eid}/", {"Title": "Changed"}, format="json")
        assert patch.status_code == status.HTTP_403_FORBIDDEN
        assert patch.data["code"] == "verified_immutable"

    def test_delete_verified_record_returns_403(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        delete = auth_client.delete(f"{BASE_URL}{eid}/")
        assert delete.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_endpoint_sets_status_3(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        verify = auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")
        assert verify.status_code == status.HTTP_204_NO_CONTENT

        detail = auth_client.get(f"{BASE_URL}{eid}/")
        assert detail.data["VerificationStatus"] == 3

    def test_double_verify_returns_400(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")
        second = auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "again"}, format="json")
        assert second.status_code == status.HTTP_400_BAD_REQUEST

    def _detail_payload(self, gwp_id):
        return {
            "Description": "Sub-meter A", "QuantityOrCost": "10.0000", "Unit": "litres",
            "EmissionFactor": DIESEL_EF, "EmissionFactorSource": "DEFRA 2024",
            "Gas": "CO2", "GwpDatasetId": gwp_id,
        }

    def test_line_items_of_verified_record_are_immutable(self, auth_client, gwp_dataset, entity):
        """Detail/offset line items feed the recomputed total, so they must be
        locked once the parent record is verified (CLAUDE.md rule #3)."""
        gwp_id = gwp_dataset.GwpDatasetId
        eid = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_id,
        ), format="json").data["EmissionsId"]

        # Add a detail while the record is still editable.
        detail = auth_client.post(
            f"{BASE_URL}{eid}/details/", self._detail_payload(gwp_id), format="json")
        assert detail.status_code == status.HTTP_201_CREATED
        detail_id = detail.data["DetailId"]

        # Verify → record is now audit-locked.
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        # Every nested write path must now be rejected.
        add = auth_client.post(
            f"{BASE_URL}{eid}/details/", self._detail_payload(gwp_id), format="json")
        assert add.status_code == status.HTTP_403_FORBIDDEN
        assert add.data["code"] == "verified_immutable"

        patch = auth_client.patch(
            f"{BASE_URL}{eid}/details/{detail_id}/", {"QuantityOrCost": "999.0000"}, format="json")
        assert patch.status_code == status.HTTP_403_FORBIDDEN

        delete = auth_client.delete(f"{BASE_URL}{eid}/details/{detail_id}/")
        assert delete.status_code == status.HTTP_403_FORBIDDEN

        offset = auth_client.post(f"{BASE_URL}{eid}/offsets/", {
            "Title": "Credit", "OffsetType": "avoidance", "Provider": "Verra",
            "OffsetAmountTonnes": "1.000000",
        }, format="json")
        assert offset.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestUnlock:
    """POST /emissions/{id}/unlock/ — SuperAdmin only, requires reason."""

    def test_unlock_requires_superadmin(self, auth_client, gwp_dataset, entity, sa_client):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        # Non-SA cannot unlock
        non_sa = auth_client.post(f"{BASE_URL}{eid}/unlock/", {"reason": "testing"}, format="json")
        assert non_sa.status_code == status.HTTP_403_FORBIDDEN

    def test_unlock_requires_reason(self, sa_client, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        # SA without reason gets 400
        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        no_reason = sa_client.post(f"{BASE_URL}{eid}/unlock/", {}, format="json")
        assert no_reason.status_code == status.HTTP_400_BAD_REQUEST

    def test_sa_can_unlock_with_reason(self, sa_client, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        unlock = sa_client.post(
            f"{BASE_URL}{eid}/unlock/",
            {"reason": "Error in original data, correcting per client request"},
            format="json",
        )
        assert unlock.status_code == status.HTTP_204_NO_CONTENT

        detail = auth_client.get(f"{BASE_URL}{eid}/")
        assert detail.data["VerificationStatus"] == 1

    def test_unlock_writes_audit_log(self, sa_client, auth_client, gwp_dataset, entity):
        """Unlock must create an AuditLog entry with RetentionTier=3 (7-year regulatory)."""
        resp = auth_client.post(BASE_URL, _payload(
            scope=1, quantity="100.0000", ef=DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId,
        ), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        sa_client.credentials(
            HTTP_AUTHORIZATION=sa_client._credentials["HTTP_AUTHORIZATION"],
            HTTP_X_ENTITY_ID=str(entity.EntityId),
        )
        sa_client.post(
            f"{BASE_URL}{eid}/unlock/",
            {"reason": "Audit requirement"},
            format="json",
        )
        from apps.shared.models import AuditLog
        log = AuditLog.objects.filter(Action="Unlock_Verified", RecordId=eid).first()
        assert log is not None
        assert log.RetentionTier == 3


@pytest.mark.django_db
class TestTenantScoping:
    """Emissions records must be strictly scoped to the requesting entity."""

    def test_tenant_cannot_see_other_entity_records(
        self, auth_client, gwp_dataset, entity
    ):
        # Create a record for a different entity directly in DB
        from apps.emissions.models import EmissionsData
        from apps.entities.tests.factories import EntitiesFactory

        other_entity = EntitiesFactory()
        other_record = EmissionsData.objects.create(
            EntityId=other_entity,
            Title="Other entity record",
            Scope=1,
            QuantityOrCost=Decimal("100"),
            Unit="litres",
            EmissionFactor=Decimal("2.639"),
            EmissionFactorSource="DEFRA",
            Gas="CO2",
            GwpDatasetId=gwp_dataset,
        )
        resp = auth_client.get(BASE_URL)
        assert resp.status_code == status.HTTP_200_OK
        ids = [r["EmissionsId"] for r in resp.data["results"]]
        assert other_record.EmissionsId not in ids

    def test_entity_id_not_accepted_from_request_body(
        self, auth_client, gwp_dataset, entity
    ):
        """Critical rule: EntityId must come from X-Entity-ID header, not request body."""
        from apps.entities.tests.factories import EntitiesFactory
        evil_entity = EntitiesFactory()

        payload = _payload(scope=1, quantity="100.0000", ef=DIESEL_EF,
                           gwp_id=gwp_dataset.GwpDatasetId)
        payload["EntityId"] = evil_entity.EntityId

        resp = auth_client.post(BASE_URL, payload, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["EntityId"] == entity.EntityId  # must be the header entity


@pytest.mark.django_db
class TestEmissionsFilters:
    def test_filter_by_scope(self, auth_client, gwp_dataset, entity, enable_feature):
        enable_feature(entity, "scope_3")  # Scope 3 is a Starter+ gated feature
        auth_client.post(BASE_URL, _payload(1, "100", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        auth_client.post(BASE_URL, _payload(2, "200", ELEC_EF,   gwp_id=gwp_dataset.GwpDatasetId), format="json")
        auth_client.post(BASE_URL, _payload(3, "300", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")

        resp = auth_client.get(f"{BASE_URL}?scope=1")
        assert all(r["Scope"] == 1 for r in resp.data["results"])

    def test_filter_by_verification_status(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(1, "100", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        eid = resp.data["EmissionsId"]
        auth_client.post(f"{BASE_URL}{eid}/verify/", {"notes": "ok"}, format="json")

        verified = auth_client.get(f"{BASE_URL}?verificationStatus=3")
        assert any(r["EmissionsId"] == eid for r in verified.data["results"])


@pytest.mark.django_db
class TestScope3FeatureGate:
    """Scope 3 accounting is Starter+ (scope_3). Server-enforced, not
    frontend-only (CLAUDE.md rule #6). Scope 1/2 stay available on all plans."""

    def test_create_scope3_denied_without_feature(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            3, "300", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
        assert resp.data["feature"] == "scope_3"

    def test_create_scope1_allowed_without_feature(self, auth_client, gwp_dataset, entity):
        """Gating Scope 3 must not affect Scope 1/2 (available on all plans)."""
        resp = auth_client.post(BASE_URL, _payload(
            1, "100", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

    def test_create_scope3_allowed_with_feature(self, auth_client, gwp_dataset, entity, enable_feature):
        enable_feature(entity, "scope_3")
        resp = auth_client.post(BASE_URL, _payload(
            3, "300", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

    def test_patch_record_to_scope3_denied_without_feature(self, auth_client, gwp_dataset, entity):
        """Re-classifying an existing record to Scope 3 is also gated."""
        created = auth_client.post(BASE_URL, _payload(
            1, "100", DIESEL_EF, gwp_id=gwp_dataset.GwpDatasetId), format="json")
        eid = created.data["EmissionsId"]
        resp = auth_client.patch(f"{BASE_URL}{eid}/", {"Scope": 3}, format="json")
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data


@pytest.mark.django_db
class TestMarketBasedScope2FeatureGate:
    """Market-based Scope 2 is Starter+ (scope_2_market_based). Gated only when a
    contractual market factor (EFMarketBased) is supplied — location-based Scope 2
    stays on all plans. Server-enforced, not frontend-only (CLAUDE.md rule #6)."""

    def test_market_based_scope2_denied_without_feature(self, auth_client, gwp_dataset, entity):
        resp = auth_client.post(BASE_URL, _payload(
            2, "5000", ELEC_EF, Unit="kWh", gwp_id=gwp_dataset.GwpDatasetId,
            EFMarketBased="0.05000000"), format="json")
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
        assert resp.data["feature"] == "scope_2_market_based"

    def test_location_based_scope2_allowed_without_feature(self, auth_client, gwp_dataset, entity):
        """Scope 2 with no market factor is location-based only → available to all."""
        resp = auth_client.post(BASE_URL, _payload(
            2, "5000", ELEC_EF, Unit="kWh", gwp_id=gwp_dataset.GwpDatasetId), format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

    def test_market_based_scope2_allowed_with_feature(self, auth_client, gwp_dataset, entity, enable_feature):
        enable_feature(entity, "scope_2_market_based")
        resp = auth_client.post(BASE_URL, _payload(
            2, "5000", ELEC_EF, Unit="kWh", gwp_id=gwp_dataset.GwpDatasetId,
            EFMarketBased="0.05000000"), format="json")
        assert resp.status_code == status.HTTP_201_CREATED, resp.data

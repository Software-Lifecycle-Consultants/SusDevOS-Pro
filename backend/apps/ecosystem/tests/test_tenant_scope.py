"""
Tenant-scope resolution for the ecosystem viewsets.

Ecosystem/Species now use TenantViewSetMixin (EntityId is a real FK to
entities.Entities). The mixin re-resolves request.entity_id after DRF (JWT)
authentication — TenantQueryMiddleware runs before authentication and leaves
request.entity_id None for token requests.

Regression test: without EntityScopeInitialMixin (the base TenantViewSetMixin
relies on), a JWT create writes EntityId=None (a NOT-NULL violation → HTTP 500)
and reads return an empty set.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

ECO_URL = "/api/ecosystems/"


def _rows(resp):
    """Return the row list whether or not the endpoint is paginated."""
    data = resp.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


def test_ecosystem_create_is_scoped_to_authenticated_entity(auth_client, entity, enable_feature):
    enable_feature(entity, "ecosystem_basic")
    resp = auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert resp.data["EntityId"] == entity.EntityId


def test_ecosystem_list_returns_own_entity_rows(auth_client, entity, enable_feature):
    enable_feature(entity, "ecosystem_basic")
    auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    resp = auth_client.get(ECO_URL)
    assert resp.status_code == status.HTTP_200_OK
    names = [row["EcosystemName"] for row in _rows(resp)]
    assert "Mangrove A" in names


def test_ecosystem_not_visible_to_other_entity(auth_client, entity, enable_feature):
    """A row created by one entity must not appear for another entity."""
    from rest_framework.test import APIClient

    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.entities.tests.factories import EntitiesFactory
    from apps.users.tests.factories import UsersFactory

    enable_feature(entity, "ecosystem_basic")
    auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")

    other_entity = EntitiesFactory(EntityName="Other Corp")
    enable_feature(other_entity, "ecosystem_basic")
    other_user = UsersFactory(
        EntityId=other_entity, email="eco-other@corp.com", username="eco_other"
    )
    other_client = APIClient()
    other_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other_user).access_token}",
        HTTP_X_ENTITY_ID=str(other_entity.EntityId),
    )

    resp = other_client.get(ECO_URL)
    assert resp.status_code == status.HTTP_200_OK
    names = [row["EcosystemName"] for row in _rows(resp)]
    assert "Mangrove A" not in names


# ── Feature gate (off by default; machinery kept and still exercised) ───────


def test_ecosystem_create_allowed_without_any_plan(auth_client, entity):
    """Ecosystem tracking ships on every plan under service-tier packaging."""
    resp = auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_ecosystem_list_allowed_without_any_plan(auth_client, entity):
    resp = auth_client.get(ECO_URL)
    assert resp.status_code == status.HTTP_200_OK, resp.data


def test_ecosystem_gate_still_denies_when_enforcement_is_switched_on(
    auth_client, entity, settings
):
    """Gating is off by default; flipping the switch must still deny."""
    settings.FEATURE_GATES_ENABLED = True
    resp = auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data["feature"] == "ecosystem_basic"


# ── Audit logging (TenantViewSetMixin behaviour gain) ───────────────────────


def test_ecosystem_create_writes_audit_log(auth_client, entity, enable_feature):
    """Adopting TenantViewSetMixin means create now writes an AuditLog row —
    EcosystemViewSet/SpeciesViewSet previously had no audit coverage at all."""
    from apps.shared.models import AuditLog

    enable_feature(entity, "ecosystem_basic")
    resp = auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

    entry = AuditLog.objects.filter(
        TableName="ecosystem", RecordId=resp.data["EcosystemId"], Action="Create",
    ).first()
    assert entry is not None
    assert entry.EntityId_id == entity.EntityId
    assert entry.Description == f"Create Ecosystem #{resp.data['EcosystemId']}"

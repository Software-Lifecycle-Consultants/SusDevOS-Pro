"""
Tenant-scope resolution for the ecosystem viewsets.

Ecosystem/Species use IntegerField EntityId and a bespoke get_queryset, so they
cannot use the full TenantViewSetMixin.  They must still re-resolve
request.entity_id after DRF (JWT) authentication — TenantQueryMiddleware runs
before authentication and leaves request.entity_id None for token requests.

Regression test: without EntityScopeInitialMixin, a JWT create writes
EntityId=None (a NOT-NULL violation → HTTP 500) and reads return an empty set.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

ECO_URL = "/api/ecosystems/"


@pytest.fixture(autouse=True)
def _grant_ecosystem_feature(entity, enable_feature):
    """Ecosystem tracking is gated (ecosystem_basic); enable it on the shared
    test entity so tenant-scope assertions are not masked by an HTTP 402."""
    enable_feature(entity, "ecosystem_basic")


def _rows(resp):
    """Return the row list whether or not the endpoint is paginated."""
    data = resp.data
    return data["results"] if isinstance(data, dict) and "results" in data else data


def test_ecosystem_create_is_scoped_to_authenticated_entity(auth_client, entity):
    resp = auth_client.post(ECO_URL, {"EcosystemName": "Mangrove A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert resp.data["EntityId"] == entity.EntityId


def test_ecosystem_list_returns_own_entity_rows(auth_client, entity):
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


def test_ecosystem_gated_without_plan_returns_402():
    """An entity with no active subscription including 'ecosystem_basic' must be
    denied with HTTP 402 feature_gated — the gate is server-enforced, not
    frontend-only (CLAUDE.md rule #6)."""
    from rest_framework.test import APIClient

    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.entities.tests.factories import EntitiesFactory
    from apps.users.tests.factories import UsersFactory

    ungated_entity = EntitiesFactory(EntityName="Free Tier Corp")
    user = UsersFactory(
        EntityId=ungated_entity, email="eco-free@corp.com", username="eco_free"
    )
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(ungated_entity.EntityId),
    )

    resp = client.get(ECO_URL)
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED
    assert resp.data.get("code") == "feature_gated"
    assert resp.data.get("feature") == "ecosystem_basic"

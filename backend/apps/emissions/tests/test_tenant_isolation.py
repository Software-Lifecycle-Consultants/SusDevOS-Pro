"""
Tenant isolation tests for the emissions API.

Verifies that a user authenticated for entity A cannot read or modify
entity B's emissions records in any way — GET list, GET detail, PATCH,
DELETE, or by spoofing the X-Entity-ID header.

Critical rule (CLAUDE.md §2): every queryset involving tenant data must
filter by request.entity_id.  TenantViewSetMixin.get_queryset() provides
this isolation — these tests verify it is actually applied.
"""

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.entities.tests.factories import EntitiesFactory
from apps.users.tests.factories import UsersFactory

EMISSIONS_URL = "/api/emissions/"
DIESEL_EF = "2.63900000"

pytestmark = pytest.mark.django_db


# ── Helpers ──────────────────────────────────────────────────────────────────


def _client_for(user, entity_id):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(entity_id),
    )
    return client


def _post_record(client, gwp_id):
    resp = client.post(
        EMISSIONS_URL,
        {
            "Title": "Diesel record",
            "Scope": 1,
            "QuantityOrCost": "100.0000",
            "Unit": "litres",
            "EmissionFactor": DIESEL_EF,
            "EmissionFactorSource": "DEFRA 2024",
            "Gas": "CO2",
            "GwpDatasetId": gwp_id,
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    return resp.data["EmissionsId"]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def two_entities(db, gwp_dataset):
    """
    Two independent entities, each with their own admin user and one seeded
    emissions record.  Returns a dict for easy destructuring in tests.
    """
    entity_a = EntitiesFactory(EntityName="Alpha Corp")
    entity_b = EntitiesFactory(EntityName="Beta Corp")

    user_a = UsersFactory(EntityId=entity_a, email="admin@alpha.com", username="admin_a")
    user_b = UsersFactory(EntityId=entity_b, email="admin@beta.com", username="admin_b")

    client_a = _client_for(user_a, entity_a.EntityId)
    client_b = _client_for(user_b, entity_b.EntityId)

    gwp_id = gwp_dataset.GwpDatasetId
    record_a = _post_record(client_a, gwp_id)
    record_b = _post_record(client_b, gwp_id)

    return {
        "entity_a": entity_a,
        "entity_b": entity_b,
        "user_a": user_a,
        "user_b": user_b,
        "client_a": client_a,
        "client_b": client_b,
        "record_a": record_a,
        "record_b": record_b,
    }


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestListIsolation:
    """GET /api/emissions/ must return only the authenticated entity's records."""

    def test_list_contains_own_records(self, two_entities):
        resp = two_entities["client_a"].get(EMISSIONS_URL)
        assert resp.status_code == status.HTTP_200_OK
        ids = [r["EmissionsId"] for r in resp.data["results"]]
        assert two_entities["record_a"] in ids

    def test_list_excludes_other_entity_records(self, two_entities):
        resp = two_entities["client_a"].get(EMISSIONS_URL)
        assert resp.status_code == status.HTTP_200_OK
        ids = [r["EmissionsId"] for r in resp.data["results"]]
        assert two_entities["record_b"] not in ids

    def test_both_entities_see_only_their_own(self, two_entities):
        """Symmetry check — the isolation works in both directions."""
        ids_a = [
            r["EmissionsId"] for r in two_entities["client_a"].get(EMISSIONS_URL).data["results"]
        ]
        ids_b = [
            r["EmissionsId"] for r in two_entities["client_b"].get(EMISSIONS_URL).data["results"]
        ]

        assert two_entities["record_a"] in ids_a
        assert two_entities["record_b"] not in ids_a

        assert two_entities["record_b"] in ids_b
        assert two_entities["record_a"] not in ids_b


class TestDetailIsolation:
    """GET /PATCH /DELETE on a specific record from the other entity must return 404."""

    def test_get_other_entity_record_returns_404(self, two_entities):
        resp = two_entities["client_a"].get(f"{EMISSIONS_URL}{two_entities['record_b']}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_patch_other_entity_record_returns_404(self, two_entities):
        resp = two_entities["client_a"].patch(
            f"{EMISSIONS_URL}{two_entities['record_b']}/",
            {"Title": "Infiltrated"},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_entity_record_returns_404(self, two_entities):
        resp = two_entities["client_a"].delete(f"{EMISSIONS_URL}{two_entities['record_b']}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_get_own_record_returns_200(self, two_entities):
        """Sanity check that the 404 is isolation, not a broken URL."""
        resp = two_entities["client_a"].get(f"{EMISSIONS_URL}{two_entities['record_a']}/")
        assert resp.status_code == status.HTTP_200_OK


class TestHeaderSpoofing:
    """
    A user who sends X-Entity-ID belonging to another entity must NOT gain
    access to that entity's data.  TenantViewSetMixin validates that the
    authenticated user has a membership in the requested entity and rejects a
    spoofed header with 403 forbidden_entity (not a silent empty result set).
    """

    def test_spoofed_header_is_rejected_with_403(self, two_entities):
        # user_a sends X-Entity-ID of entity_b — must be denied outright.
        spoofed = _client_for(two_entities["user_a"], two_entities["entity_b"].EntityId)
        resp = spoofed.get(EMISSIONS_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data.get("code") == "forbidden_entity"

    def test_spoofed_header_cannot_get_detail_of_other_entity(self, two_entities):
        spoofed = _client_for(two_entities["user_a"], two_entities["entity_b"].EntityId)
        resp = spoofed.get(f"{EMISSIONS_URL}{two_entities['record_b']}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data.get("code") == "forbidden_entity"


class TestUnauthenticated:
    """Unauthenticated requests must be rejected before any data is returned."""

    def test_unauthenticated_list_returns_401(self, api_client):
        resp = api_client.get(EMISSIONS_URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_detail_returns_401(self, api_client, two_entities):
        resp = api_client.get(f"{EMISSIONS_URL}{two_entities['record_a']}/")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

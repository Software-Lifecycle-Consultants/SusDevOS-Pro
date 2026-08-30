"""Land-parcel access under service-tier packaging.

Per-capability gating is OFF by default (settings.FEATURE_GATES_ENABLED): plans are
sold on service and hosting tiers, so land parcels are available to every
authenticated tenant. ``land_parcel_gis`` returning 402 to a paying customer was the
bug that prompted the change.

Both halves are pinned here. The first two tests are the live contract. The last two
keep the gate machinery honest — it is switched off, not deleted, so reintroducing
gating is a settings flip rather than a rebuild, and these fail if the mechanism rots.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

PARCELS_URL = "/api/land-parcels/"


def test_create_land_parcel_allowed_without_any_plan(auth_client, entity):
    """No subscription, no features, no 402 — the default the product ships with."""
    resp = auth_client.post(PARCELS_URL, {"ParcelName": "Field A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert resp.data["EntityId"] == entity.EntityId


def test_list_land_parcels_allowed_without_any_plan(auth_client, entity):
    resp = auth_client.get(PARCELS_URL)
    assert resp.status_code == status.HTTP_200_OK, resp.data


def test_gate_still_denies_when_enforcement_is_switched_on(auth_client, entity, settings):
    """The kept machinery must still work if gating is ever turned back on."""
    settings.FEATURE_GATES_ENABLED = True
    resp = auth_client.post(PARCELS_URL, {"ParcelName": "Field A"}, format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data["feature"] == "land_parcel_gis"


def test_gate_admits_entitled_entity_when_enforcement_is_switched_on(
    auth_client, entity, enable_feature, settings
):
    settings.FEATURE_GATES_ENABLED = True
    enable_feature(entity, "land_parcel_gis")
    resp = auth_client.post(PARCELS_URL, {"ParcelName": "Field A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

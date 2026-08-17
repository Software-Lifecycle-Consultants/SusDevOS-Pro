"""Server-side feature-gate tests for the land-parcel viewset.

CLAUDE.md rule #6: feature gates are server-enforced, never frontend-only.
GIS land-parcel mapping is Professional+ (``land_parcel_gis``), so an entity
without that feature must be denied at the API even if the frontend hides it.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

PARCELS_URL = "/api/land-parcels/"


def test_create_land_parcel_denied_without_feature(auth_client, entity):
    resp = auth_client.post(PARCELS_URL, {"ParcelName": "Field A"}, format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data


def test_list_land_parcels_denied_without_feature(auth_client, entity):
    resp = auth_client.get(PARCELS_URL)
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data


def test_create_land_parcel_allowed_with_feature(auth_client, entity, enable_feature):
    enable_feature(entity, "land_parcel_gis")
    resp = auth_client.post(PARCELS_URL, {"ParcelName": "Field A"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert resp.data["EntityId"] == entity.EntityId

"""
Server-side enforcement of the land_parcel_gis feature gate (CLAUDE.md rule #6).

GIS land-parcel mapping is a Professional+ feature (spec/pricing.md). The gate is
geometry-conditional: supplying a BoundaryGeoJSON polygon requires the feature,
while a non-GIS parcel (no geometry) stays available on any plan.
"""
from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.entities.tests.factories import EntitiesFactory
from apps.users.tests.factories import SuperAdminFactory, UsersFactory

pytestmark = pytest.mark.django_db

PARCELS_URL = "/api/land-parcels/"
_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
}


def _client_for(user, entity_id):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(entity_id),
    )
    return client


@pytest.fixture
def entity_client():
    entity = EntitiesFactory(EntityName="Land Corp")
    user = UsersFactory(EntityId=entity, email="land@corp.com", username="land_user")
    return entity, _client_for(user, entity.EntityId)


def test_parcel_with_geometry_gated_without_feature(entity_client):
    _entity, client = entity_client
    resp = client.post(
        PARCELS_URL,
        {"ParcelName": "GIS parcel", "BoundaryGeoJSON": _POLYGON},
        format="json",
    )
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data.get("code") == "feature_gated"
    assert resp.data.get("feature") == "land_parcel_gis"


def test_parcel_with_geometry_allowed_with_feature(entity_client, enable_feature):
    entity, client = entity_client
    enable_feature(entity, "land_parcel_gis")
    resp = client.post(
        PARCELS_URL,
        {"ParcelName": "GIS parcel", "BoundaryGeoJSON": _POLYGON},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_parcel_without_geometry_not_gated(entity_client):
    """A non-GIS parcel (no BoundaryGeoJSON) is available on any plan."""
    _entity, client = entity_client
    resp = client.post(PARCELS_URL, {"ParcelName": "Plain parcel"}, format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_superadmin_bypasses_gis_gate():
    sa = SuperAdminFactory(email="sa-land@susdevos.com", username="sa_land")
    entity = EntitiesFactory(EntityName="SA Land Corp")
    client = _client_for(sa, entity.EntityId)
    resp = client.post(
        PARCELS_URL,
        {"ParcelName": "SA GIS parcel", "BoundaryGeoJSON": _POLYGON},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

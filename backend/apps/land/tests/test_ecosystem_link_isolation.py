"""
Tenant isolation tests for the land-parcel → ecosystem linking endpoint.

Regression coverage for CLAUDE.md critical rule #2: a client must never be
able to read or link another tenant's ecosystem by supplying its id in the
request body. The parcel is tenant-scoped by TenantViewSetMixin; every
ecosystem operation on it must be scoped to the same entity.
"""

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.ecosystem.models import Ecosystem
from apps.entities.tests.factories import EntitiesFactory
from apps.land.models import LandParcelEcosystems, LandParcels
from apps.users.tests.factories import UsersFactory

pytestmark = pytest.mark.django_db


def _client_for(user, entity_id):
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(entity_id),
    )
    return client


@pytest.fixture
def two_tenants(db, enable_feature):
    entity_a = EntitiesFactory(EntityName="Alpha Corp")
    entity_b = EntitiesFactory(EntityName="Beta Corp")
    user_a = UsersFactory(EntityId=entity_a, email="admin@alpha.com", username="land_a")
    # land-parcel routes are gated (land_parcel_gis); grant it so the tenant
    # isolation behaviour under test is reachable.
    enable_feature(entity_a, "land_parcel_gis")

    parcel_a = LandParcels.objects.create(EntityId=entity_a, ParcelName="Alpha parcel")
    eco_b = Ecosystem.objects.create(EntityId_id=entity_b.EntityId, EcosystemName="Beta wetland")

    return {
        "client_a": _client_for(user_a, entity_a.EntityId),
        "parcel_a": parcel_a,
        "eco_b": eco_b,
    }


def _url(parcel):
    return f"/api/land-parcels/{parcel.LandParcelId}/ecosystems/"


def test_cannot_link_other_tenant_ecosystem(two_tenants):
    """POSTing another tenant's EcosystemId must be rejected and create no link."""
    resp = two_tenants["client_a"].post(
        _url(two_tenants["parcel_a"]),
        {"EcosystemId": two_tenants["eco_b"].EcosystemId},
        format="json",
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND, resp.data
    assert not LandParcelEcosystems.objects.filter(
        LandParcelId=two_tenants["parcel_a"],
        EcosystemId=two_tenants["eco_b"],
    ).exists()


def test_can_link_own_ecosystem(two_tenants):
    """Sanity check — linking an ecosystem in the parcel's own entity works."""
    parcel = two_tenants["parcel_a"]
    own_eco = Ecosystem.objects.create(
        EntityId_id=parcel.EntityId_id, EcosystemName="Alpha meadow"
    )
    resp = two_tenants["client_a"].post(
        _url(parcel), {"EcosystemId": own_eco.EcosystemId}, format="json"
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    assert LandParcelEcosystems.objects.filter(
        LandParcelId=parcel, EcosystemId=own_eco
    ).exists()


def test_get_excludes_cross_tenant_ecosystem(two_tenants):
    """
    Even if a cross-tenant link somehow exists in the join table, the GET must
    not surface the other tenant's ecosystem data.
    """
    parcel = two_tenants["parcel_a"]
    LandParcelEcosystems.objects.create(
        LandParcelId=parcel, EcosystemId=two_tenants["eco_b"]
    )
    resp = two_tenants["client_a"].get(_url(parcel))
    assert resp.status_code == status.HTTP_200_OK
    returned_ids = [e["EcosystemId"] for e in resp.data]
    assert two_tenants["eco_b"].EcosystemId not in returned_ids

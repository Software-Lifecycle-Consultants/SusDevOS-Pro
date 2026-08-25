"""
Entities API tests.

Covers:
  - GET  /api/entities/    (SA sees all; Admin sees own + related)
  - POST /api/entities/    (SA only; creates entity + admin user)
  - GET  /api/entities/{id}/
  - PATCH /api/entities/{id}/
  - DELETE /api/entities/{id}/ (soft delete, SA only)
  - Tenant scoping: admin cannot see other entities
"""
from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.entities.models import Entities
from apps.entities.tests.factories import EntitiesFactory
from apps.users.tests.factories import UsersFactory


@pytest.mark.django_db
class TestEntitiesList:
    URL = "/api/entities/"

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_superadmin_sees_all_entities(self, sa_client):
        EntitiesFactory.create_batch(3)
        resp = sa_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] >= 3

    def test_admin_sees_only_own_entity(self, auth_client, entity):
        # Create a second entity the admin should NOT see
        other = EntitiesFactory(EntityName="Other Corp")
        resp = auth_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        ids = [r["EntityId"] for r in resp.data["results"]]
        assert entity.EntityId in ids
        assert other.EntityId not in ids

    def test_returns_pagination_envelope(self, sa_client):
        resp = sa_client.get(self.URL)
        assert "count" in resp.data
        assert "results" in resp.data


@pytest.mark.django_db
class TestEntityCreate:
    URL = "/api/entities/"

    def test_sa_can_create_entity(self, sa_client, db):
        """POST /entities/ creates entity + initial admin user."""
        # Seed the free plan so EntityCreateSerializer can assign a subscription
        from apps.billing.models import Plans
        plan, _ = Plans.objects.get_or_create(
            PlanKey="free",
            defaults={
                "PlanName": "Free", "PriceMonthlyGBP": 0, "PriceAnnualGBP": 0,
                "MaxEntities": 1, "MaxUsersPerEntity": 1, "MaxReportingYears": 1,
                "MaxApiCallsPerDay": 0, "SupportTier": "docs",
            },
        )
        resp = sa_client.post(self.URL, {
            "EntityName":          "New Dev Co",
            "EntityType":          1,
            "Country":             "United Kingdom",
            "BaseCurrency":        "GBP",
            "initial_admin_email":    "admin@newdev.co",
            "initial_admin_username": "newdev_admin",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Entities.objects.filter(EntityName="New Dev Co").exists()
        # Initial admin user was created
        from apps.users.models import Users
        assert Users.objects.filter(email="admin@newdev.co").exists()

    def test_non_sa_cannot_create_entity(self, auth_client):
        resp = auth_client.post(self.URL, {
            "EntityName": "Unauthorised",
            "initial_admin_email": "x@y.com",
            "initial_admin_username": "x",
        }, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEntityDetail:
    def test_sa_can_retrieve_any_entity(self, sa_client):
        e = EntitiesFactory()
        resp = sa_client.get(f"/api/entities/{e.EntityId}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["EntityId"] == e.EntityId

    def test_admin_can_retrieve_own_entity(self, auth_client, entity):
        resp = auth_client.get(f"/api/entities/{entity.EntityId}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_admin_cannot_retrieve_other_entity(self, auth_client):
        other = EntitiesFactory()
        resp = auth_client.get(f"/api/entities/{other.EntityId}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestEntityUpdate:
    def test_patch_updates_name(self, sa_client):
        e = EntitiesFactory(EntityName="Old Name")
        resp = sa_client.patch(
            f"/api/entities/{e.EntityId}/",
            {"EntityName": "New Name"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        e.refresh_from_db()
        assert e.EntityName == "New Name"


@pytest.mark.django_db
class TestEntitySoftDelete:
    def test_sa_soft_deletes_entity(self, sa_client):
        e = EntitiesFactory()
        resp = sa_client.delete(f"/api/entities/{e.EntityId}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        e.refresh_from_db()
        assert e.Status == 4

    def test_soft_deleted_entity_excluded_from_list(self, sa_client):
        e = EntitiesFactory()
        sa_client.delete(f"/api/entities/{e.EntityId}/")
        resp = sa_client.get("/api/entities/")
        ids = [r["EntityId"] for r in resp.data["results"]]
        assert e.EntityId not in ids

    def test_non_sa_cannot_delete(self, auth_client, entity):
        resp = auth_client.delete(f"/api/entities/{entity.EntityId}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestEntitySettings:
    def test_get_settings(self, auth_client, entity):
        resp = auth_client.get(f"/api/entities/{entity.EntityId}/settings/")
        assert resp.status_code == status.HTTP_200_OK
        assert "BaseCurrency" in resp.data
        assert "ShareEmissionsWithPartners" in resp.data

    def test_patch_settings(self, auth_client, entity):
        resp = auth_client.patch(
            f"/api/entities/{entity.EntityId}/settings/",
            {"ShareEmissionsWithPartners": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        entity.refresh_from_db()
        assert entity.ShareEmissionsWithPartners is True


def _member_client(entity):
    """Authenticated APIClient for a non-admin member of `entity`."""
    from rest_framework_simplejwt.tokens import RefreshToken

    member = UsersFactory(EntityId=entity, email="member@testcorp.com", username="member1")
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {str(RefreshToken.for_user(member).access_token)}",
        HTTP_X_ENTITY_ID=str(entity.EntityId),
    )
    return client


@pytest.mark.django_db
class TestEntitySettingsAuthz:
    """A non-admin member must not be able to change entity settings."""

    def test_member_cannot_patch_settings(self, entity):
        client = _member_client(entity)
        resp = client.patch(
            f"/api/entities/{entity.EntityId}/settings/",
            {"ShareEmissionsWithPartners": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        entity.refresh_from_db()
        assert entity.ShareEmissionsWithPartners is not True

    def test_admin_can_still_patch_settings(self, auth_client, entity):
        resp = auth_client.patch(
            f"/api/entities/{entity.EntityId}/settings/",
            {"ShareEmissionsWithPartners": True},
            format="json",
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestRetiredApiKeyRoutes:
    """Customer API-key routes must not exist, even for entity admins."""

    def test_list_route_returns_404(self, auth_client, entity):
        resp = auth_client.get(f"/api/entities/{entity.EntityId}/api-keys/")

        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_create_route_returns_404_without_creating_key(self, auth_client, entity):
        from apps.shared.models import EntityApiKeys

        before = EntityApiKeys.objects.count()
        resp = auth_client.post(
            f"/api/entities/{entity.EntityId}/api-keys/",
            {"AuthorizedByFor": "retired integration"},
            format="json",
        )

        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert EntityApiKeys.objects.count() == before

    def test_delete_route_returns_404_without_revoking_key(self, auth_client, entity):
        from apps.entities.models import EntityApiKeysIntermediary
        from apps.shared.tests.factories import EntityApiKeysFactory

        key = EntityApiKeysFactory(EntityId=entity.EntityId, Status=1)
        EntityApiKeysIntermediary.objects.create(EntityId=entity, ApiKeyId=key)

        resp = auth_client.delete(
            f"/api/entities/{entity.EntityId}/api-keys/{key.ApiKeyId}/"
        )

        assert resp.status_code == status.HTTP_404_NOT_FOUND
        key.refresh_from_db()
        assert key.Status == 1

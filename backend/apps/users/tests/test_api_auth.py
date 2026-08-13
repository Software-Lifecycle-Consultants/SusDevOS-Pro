"""
Auth API tests.

Covers:
  - POST /api/auth/login  (valid, invalid, disabled)
  - POST /api/auth/logout (revokes token)
  - GET  /api/auth/me     (profile + privilege map)
  - POST /api/auth/refresh (requires HttpOnly cookie)
  - POST /api/auth/forgot-password (always 204, no email leak)
  - POST /api/auth/reset-password
"""

from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.users.tests.factories import SuperAdminFactory, UsersFactory


@pytest.mark.django_db
class TestLogin:
    URL = "/api/auth/login"

    def test_valid_credentials_returns_token(self):
        user = SuperAdminFactory(email="login@test.com")
        client = APIClient()
        resp = client.post(self.URL, {"username": "login@test.com", "password": "testpassword123!"})
        assert resp.status_code == status.HTTP_200_OK
        assert "access_token" in resp.data
        assert resp.data["user"]["email"] == "login@test.com"

    def test_email_or_username_both_work(self, db):
        """Users can log in with either email or username."""
        user = UsersFactory(email="user@corp.com", username="corp_user")
        client = APIClient()
        by_email    = client.post(self.URL, {"username": "user@corp.com",  "password": "testpassword123!"})
        by_username = client.post(self.URL, {"username": "corp_user", "password": "testpassword123!"})
        assert by_email.status_code    == status.HTTP_200_OK
        assert by_username.status_code == status.HTTP_200_OK

    def test_wrong_password_returns_400(self, db):
        SuperAdminFactory(email="bad@test.com")
        resp = APIClient().post(self.URL, {"username": "bad@test.com", "password": "wrongpassword"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_user_returns_400(self, db):
        resp = APIClient().post(self.URL, {"username": "nobody@test.com", "password": "any"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_disabled_user_returns_400(self, db, entity):
        user = UsersFactory(EntityId=entity, is_active=False, Status=4)
        resp = APIClient().post(self.URL, {"username": user.email, "password": "testpassword123!"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_refresh_cookie_is_set(self, db):
        SuperAdminFactory(email="cookie@test.com")
        resp = APIClient().post(self.URL, {"username": "cookie@test.com", "password": "testpassword123!"})
        assert "refresh_token" in resp.cookies


@pytest.mark.django_db
class TestMe:
    URL = "/api/auth/me"

    def test_authenticated_returns_user_and_privileges(self, auth_client, admin_user):
        resp = auth_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["user"]["UserId"] == admin_user.UserId
        assert "privileges" in resp.data
        # Privileges is a dict of interface_key → bool
        assert isinstance(resp.data["privileges"], dict)

    def test_superadmin_gets_all_privileges_true(self, sa_client, db):
        # Seed at least one module + interface so the privilege map is non-empty
        from apps.users.tests.factories import InterfacesFactory, ModulesFactory
        m = ModulesFactory(ModuleKey="emissions_test")
        InterfacesFactory(ModuleId=m, InterfaceKey="view_emissions_test")

        resp = sa_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        privs = resp.data["privileges"]
        assert len(privs) > 0
        assert all(v is True for v in privs.values())

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogout:
    LOGIN_URL  = "/api/auth/login"
    LOGOUT_URL = "/api/auth/logout"
    ME_URL     = "/api/auth/me"

    def test_logout_revokes_access_token(self):
        """After logout, the same access token must be rejected."""
        user = SuperAdminFactory(email="logout@test.com")
        client = APIClient()

        login = client.post(self.LOGIN_URL, {"username": "logout@test.com", "password": "testpassword123!"})
        token = login.data["access_token"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # /me works before logout
        assert client.get(self.ME_URL).status_code == status.HTTP_200_OK

        # Logout
        assert client.post(self.LOGOUT_URL).status_code == status.HTTP_204_NO_CONTENT

        # /me is now blocked
        assert client.get(self.ME_URL).status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestForgotPassword:
    URL = "/api/auth/forgot-password"

    def test_always_returns_204_for_existing_email(self, db):
        UsersFactory(email="exists@corp.com")
        resp = APIClient().post(self.URL, {"email": "exists@corp.com"})
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_always_returns_204_for_nonexistent_email(self, db):
        """Must not reveal whether email exists — always 204."""
        resp = APIClient().post(self.URL, {"email": "nobody@nowhere.com"})
        assert resp.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestResetPassword:
    RESET_URL = "/api/auth/reset-password"
    LOGIN_URL = "/api/auth/login"

    def test_valid_token_sets_new_password(self, db):
        from datetime import timedelta

        from django.utils import timezone

        from apps.users.models import PasswordResetTokens

        user = UsersFactory(email="reset@corp.com")
        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() + timedelta(hours=1),
        )
        resp = APIClient().post(self.RESET_URL, {
            "token": str(token.Token),
            "new_password": "NewSecurePass99!",
        })
        assert resp.status_code == status.HTTP_204_NO_CONTENT

        # Can log in with new password
        login = APIClient().post(self.LOGIN_URL, {
            "username": "reset@corp.com",
            "password": "NewSecurePass99!",
        })
        assert login.status_code == status.HTTP_200_OK

    def test_expired_token_rejected(self, db):
        from datetime import timedelta

        from django.utils import timezone

        from apps.users.models import PasswordResetTokens

        user = UsersFactory(email="expired@corp.com")
        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() - timedelta(seconds=1),
        )
        resp = APIClient().post(self.RESET_URL, {
            "token": str(token.Token),
            "new_password": "SomeNewPass99!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_used_token_rejected(self, db):
        from datetime import timedelta

        from django.utils import timezone

        from apps.users.models import PasswordResetTokens

        user = UsersFactory(email="used@corp.com")
        token = PasswordResetTokens.objects.create(
            UserId=user,
            ExpiresAt=timezone.now() + timedelta(hours=1),
            UsedAt=timezone.now(),
        )
        resp = APIClient().post(self.RESET_URL, {
            "token": str(token.Token),
            "new_password": "SomeNewPass99!",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSignup:
    URL = "/api/auth/signup"

    @pytest.fixture(autouse=True)
    def seed_required_data(self, db):
        """Ensure Free plan and Admin role exist (idempotent with seed commands)."""
        from apps.billing.models import Plans
        from apps.users.models import Roles

        Plans.objects.get_or_create(
            PlanKey="free",
            defaults={
                "PlanName": "Free", "PriceMonthlyGBP": 0, "PriceAnnualGBP": 0,
                "MaxEntities": 1, "MaxUsersPerEntity": 1, "MaxReportingYears": 1,
                "SupportTier": "docs",
            },
        )
        Roles.objects.get_or_create(
            RoleKey="admin",
            defaults={"RoleName": "Admin", "Description": "Organisation admin"},
        )

    VALID = {
        "first_name":     "Alice",
        "last_name":      "Green",
        "email":          "alice@newco.com",
        "company_name":   "NewCo Ltd",
        "password":       "SecurePass99!",
        "accepted_terms": True,
    }

    def test_creates_entity_user_and_subscription(self, db):
        from apps.billing.models import EntitySubscriptions
        from apps.entities.models import Entities
        from apps.users.models import Users

        resp = APIClient().post(self.URL, self.VALID)
        assert resp.status_code == 201
        assert "access_token" in resp.data

        user = Users.objects.get(email="alice@newco.com")
        assert user.FirstName == "Alice"
        assert user.is_active is True
        assert Entities.objects.filter(EntityName="NewCo Ltd").exists()
        assert EntitySubscriptions.objects.filter(EntityId_id=user.EntityId_id).exists()

    def test_response_sets_refresh_cookie(self, db):
        resp = APIClient().post(self.URL, self.VALID)
        assert resp.status_code == 201
        assert "refresh_token" in resp.cookies

    def test_user_gets_admin_role(self, db):
        from apps.users.models import Users
        APIClient().post(self.URL, self.VALID)
        user = Users.objects.get(email="alice@newco.com")
        role = user.user_roles.filter(Status=1).select_related("RoleId").first()
        assert role is not None
        assert role.RoleId.RoleKey == "admin"

    def test_subscription_is_free_plan(self, db):
        from apps.billing.models import EntitySubscriptions
        from apps.users.models import Users
        APIClient().post(self.URL, self.VALID)
        user = Users.objects.get(email="alice@newco.com")
        sub = EntitySubscriptions.objects.get(EntityId_id=user.EntityId_id)
        assert sub.PlanId.PlanKey == "free"
        assert sub.Status == "active"

    def test_duplicate_email_rejected(self, db):
        APIClient().post(self.URL, self.VALID)
        resp = APIClient().post(self.URL, self.VALID)
        assert resp.status_code == 400

    def test_terms_not_accepted_rejected(self, db):
        payload = {**self.VALID, "email": "b@test.com", "accepted_terms": False}
        resp = APIClient().post(self.URL, payload)
        assert resp.status_code == 400

    def test_short_password_rejected(self, db):
        payload = {**self.VALID, "email": "c@test.com", "password": "short"}
        resp = APIClient().post(self.URL, payload)
        assert resp.status_code == 400

    def test_missing_fields_rejected(self, db):
        resp = APIClient().post(self.URL, {"email": "d@test.com", "password": "SecurePass99!"})
        assert resp.status_code == 400

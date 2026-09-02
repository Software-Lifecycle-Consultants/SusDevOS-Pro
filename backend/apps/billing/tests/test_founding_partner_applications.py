from django.core import mail
from django.core.cache import cache
from django.test import override_settings

import pytest

from apps.billing.models import FoundingPartnerApplication

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


APPLICATION = {
    "FullName": "Jane Smith",
    "Email": "Jane@Example.com",
    "CompanyName": "Example Infrastructure Ltd",
    "Role": "Sustainability Manager",
    "Website": "https://example.com",
    "UseCase": "GHG inventory",
    "LiveProject": "A live infrastructure project entering its 2026 reporting cycle.",
    "ExpectedUsers": 6,
    "CurrentTooling": "Spreadsheets",
    "Message": "We can begin within 30 days.",
    "ConsentToFollowUp": True,
}


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_public_application_is_stored_and_notified(api_client):
    response = api_client.post(
        "/api/public/founding-partner-applications/",
        APPLICATION,
        format="json",
    )

    assert response.status_code == 201
    application = FoundingPartnerApplication.objects.get()
    assert application.Email == "jane@example.com"
    assert application.Status == "new"
    assert len(mail.outbox) == 1
    assert "Example Infrastructure Ltd" in mail.outbox[0].subject
    assert mail.outbox[0].reply_to == ["jane@example.com"]


def test_application_requires_follow_up_consent(api_client):
    response = api_client.post(
        "/api/public/founding-partner-applications/",
        {**APPLICATION, "ConsentToFollowUp": False},
        format="json",
    )

    assert response.status_code == 400
    assert FoundingPartnerApplication.objects.count() == 0


def test_application_enforces_offer_user_limit(api_client):
    response = api_client.post(
        "/api/public/founding-partner-applications/",
        {**APPLICATION, "ExpectedUsers": 11},
        format="json",
    )

    assert response.status_code == 400
    assert FoundingPartnerApplication.objects.count() == 0

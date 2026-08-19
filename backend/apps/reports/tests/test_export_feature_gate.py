"""
Server-side enforcement of the report_csv_json_export feature gate
(CLAUDE.md rule #6).

CSV/JSON export is a Starter+ feature (spec/pricing.md). PDF reports are
available on every plan (watermarked on Free), so PDF creation is never blocked
here — the branding tier is applied when the file is rendered.
"""
from rest_framework import status
from rest_framework.test import APIClient

import pytest

from apps.entities.tests.factories import EntitiesFactory
from apps.users.tests.factories import UsersFactory

pytestmark = pytest.mark.django_db

REPORTS_URL = "/api/reports/"


def _client_for(entity):
    from rest_framework_simplejwt.tokens import RefreshToken

    user = UsersFactory(
        EntityId=entity,
        email=f"rep-{entity.EntityId}@corp.com",
        username=f"rep_{entity.EntityId}",
    )
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}",
        HTTP_X_ENTITY_ID=str(entity.EntityId),
    )
    return client


def _payload(fmt):
    return {"ReportType": "emissions_summary", "Format": fmt, "Parameters": {}}


def test_csv_export_gated_without_plan():
    client = _client_for(EntitiesFactory(EntityName="Free Reports Corp"))
    resp = client.post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data.get("code") == "feature_gated"
    assert resp.data.get("feature") == "report_csv_json_export"


def test_json_export_gated_without_plan():
    client = _client_for(EntitiesFactory(EntityName="Free Reports Corp 2"))
    resp = client.post(REPORTS_URL, _payload("json"), format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data.get("feature") == "report_csv_json_export"


def test_csv_export_allowed_with_plan(enable_feature):
    entity = EntitiesFactory(EntityName="Starter Reports Corp")
    enable_feature(entity, "report_csv_json_export")
    resp = _client_for(entity).post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_pdf_export_not_gated():
    """PDF reports are available on every plan (watermarked on Free)."""
    client = _client_for(EntitiesFactory(EntityName="Free PDF Corp"))
    resp = client.post(REPORTS_URL, _payload("pdf"), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

"""Server-side feature-gate tests for report export formats.

CLAUDE.md rule #6: feature gates are server-enforced, never frontend-only.
CSV/JSON export is Starter+ (``report_csv_json_export``); PDF stays available
on all plans (Free gets watermarked PDF).
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

REPORTS_URL = "/api/reports/"


def _payload(fmt):
    return {"ReportType": "emissions_summary", "Format": fmt, "Parameters": {}}


def test_csv_export_denied_without_feature(auth_client, entity):
    resp = auth_client.post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data["feature"] == "report_csv_json_export"


def test_json_export_denied_without_feature(auth_client, entity):
    resp = auth_client.post(REPORTS_URL, _payload("json"), format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data


def test_pdf_export_allowed_without_feature(auth_client, entity):
    """PDF is available on all plans, so it must not be gated."""
    resp = auth_client.post(REPORTS_URL, _payload("pdf"), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_csv_export_allowed_with_feature(auth_client, entity, enable_feature):
    enable_feature(entity, "report_csv_json_export")
    resp = auth_client.post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

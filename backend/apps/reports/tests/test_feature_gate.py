"""Report export formats under service-tier packaging.

Per-capability gating is OFF by default (settings.FEATURE_GATES_ENABLED), so CSV and
JSON export are available to every authenticated tenant alongside PDF. The last two
tests keep the ``report_csv_json_export`` gate machinery exercised so it still works
if enforcement is switched back on.
"""
from rest_framework import status

import pytest

pytestmark = pytest.mark.django_db

REPORTS_URL = "/api/reports/"


def _payload(fmt):
    return {"ReportType": "emissions_summary", "Format": fmt, "Parameters": {}}


@pytest.mark.parametrize("fmt", ["csv", "json", "pdf"])
def test_every_export_format_allowed_without_any_plan(auth_client, entity, fmt):
    resp = auth_client.post(REPORTS_URL, _payload(fmt), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data


def test_gate_still_denies_csv_when_enforcement_is_switched_on(auth_client, entity, settings):
    settings.FEATURE_GATES_ENABLED = True
    resp = auth_client.post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.data
    assert resp.data["feature"] == "report_csv_json_export"


def test_gate_admits_entitled_entity_when_enforcement_is_switched_on(
    auth_client, entity, enable_feature, settings
):
    settings.FEATURE_GATES_ENABLED = True
    enable_feature(entity, "report_csv_json_export")
    resp = auth_client.post(REPORTS_URL, _payload("csv"), format="json")
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

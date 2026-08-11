"""
Tests for the Verra registry sync task (tasks/integrations/verra.py).

Focus: a truncated/empty CSV download must not mass-invalidate genuinely-valid
pending credits. Because the requery only reconsiders pending/unverified rows,
such an invalidation would be permanent, so the task aborts on an empty registry.
"""
from decimal import Decimal
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


class _FakeResponse:
    """Minimal stand-in for requests.get(..., stream=True)."""

    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    def iter_lines(self):
        return iter(self._lines)


def _pending_verra_offset(entity, gwp_dataset, serial="VCS-123"):
    from apps.emissions.models import EmissionsData, EmissionsOffsets

    record = EmissionsData.objects.create(
        EntityId=entity, Title="rec", Scope=1,
        QuantityOrCost=Decimal("100"), Unit="litres",
        EmissionFactor=Decimal("2.639"), EmissionFactorSource="DEFRA 2024",
        Gas="CO2", GwpDatasetId=gwp_dataset,
    )
    return EmissionsOffsets.objects.create(
        EntityId=entity, EmissionsId=record, Title="Credit",
        OffsetType="vcs", Provider="Verra", OffsetAmountTonnes=Decimal("1"),
        CreditRegistry="verra", CreditSerialNumber=serial,
        RegistryValidationStatus="pending",
    )


def test_empty_csv_does_not_invalidate_pending_offsets(entity, gwp_dataset):
    from tasks.integrations.verra import sync_verra_registry

    offset = _pending_verra_offset(entity, gwp_dataset)

    # Header row only — no data rows → zero serials parsed.
    header_only = [b"Serial Number,Retirement Beneficiary"]

    with patch("tasks.integrations.verra.settings") as mock_settings, \
         patch("tasks.integrations.verra.requests.get", return_value=_FakeResponse(header_only)):
        mock_settings.VERRA_CSV_URL = "https://example.test/verra.csv"
        result = sync_verra_registry()

    assert result.get("invalidated", 0) == 0
    offset.refresh_from_db()
    # Must remain pending — NOT flipped to the sticky "invalid" state.
    assert offset.RegistryValidationStatus == "pending"


def test_valid_serial_still_validates(entity, gwp_dataset):
    from tasks.integrations.verra import sync_verra_registry

    offset = _pending_verra_offset(entity, gwp_dataset, serial="VCS-999")
    rows = [
        b"Serial Number,Retirement Beneficiary",
        b"VCS-999,Acme Corp",
    ]

    with patch("tasks.integrations.verra.settings") as mock_settings, \
         patch("tasks.integrations.verra.requests.get", return_value=_FakeResponse(rows)):
        mock_settings.VERRA_CSV_URL = "https://example.test/verra.csv"
        result = sync_verra_registry()

    assert result["validated"] == 1
    offset.refresh_from_db()
    assert offset.RegistryValidationStatus == "valid"

"""
Unit tests for the emissions calculation service (apps/emissions/services.py),
focused on the dual-method Scope 2 and biogenic CO2 logic added in the
nature/MRV pass. EmissionsData.save() triggers compute_emissions(), so creating
a record exercises the full server-side path.
"""
from decimal import Decimal

import pytest

pytestmark = pytest.mark.django_db


def _emission(entity, gwp_dataset, **kwargs):
    from apps.emissions.models import EmissionsData
    defaults = {
        "EntityId": entity, "Title": "rec", "Scope": 1,
        "QuantityOrCost": Decimal("1000"), "Unit": "kWh",
        "EmissionFactor": Decimal("0.5"), "EmissionFactorSource": "test",
        "Gas": "CO2", "GwpDatasetId": gwp_dataset,
    }
    defaults.update(kwargs)
    return EmissionsData.objects.create(**defaults)


def test_scope2_dual_method_uses_separate_factors(entity, gwp_dataset):
    rec = _emission(
        entity, gwp_dataset, Scope=2,
        EFLocationBased=Decimal("0.5"), EFMarketBased=Decimal("0.1"),
    )
    # 1000 kWh × each factor
    assert rec.EmissionsAmountLocationBased == Decimal("500.0000")
    assert rec.EmissionsAmountMarketBased == Decimal("100.0000")
    assert rec.EmissionsAmountLocationBased != rec.EmissionsAmountMarketBased


def test_scope2_primary_amount_is_market_based(entity, gwp_dataset):
    """Primary EmissionsAmount uses market-based when available (GHG Protocol Scope 2)."""
    rec = _emission(
        entity, gwp_dataset, Scope=2,
        EFLocationBased=Decimal("0.5"), EFMarketBased=Decimal("0.1"),
    )
    assert rec.EmissionsAmount == Decimal("100.0000")
    assert rec.EmissionsAmountTonnes == Decimal("0.100000")


def test_scope2_market_falls_back_to_location_when_absent(entity, gwp_dataset):
    rec = _emission(entity, gwp_dataset, Scope=2, EFLocationBased=Decimal("0.5"))
    assert rec.EmissionsAmountLocationBased == Decimal("500.0000")
    assert rec.EmissionsAmountMarketBased == Decimal("500.0000")


def test_scope2_fallback_amounts_refresh_on_edit(entity, gwp_dataset):
    """A legacy Scope 2 record with no explicit EF* factors must recompute all
    amounts when re-saved. Regression: the fallback branches previously only ran
    when the field was still None, so an edit left LB/MB (and the primary
    EmissionsAmount derived from MB) at their stale first-save values."""
    rec = _emission(
        entity, gwp_dataset, Scope=2,
        QuantityOrCost=Decimal("100"), EmissionFactor=Decimal("0.5"),
    )
    assert rec.EmissionsAmount == Decimal("50.0000")
    assert rec.EmissionsAmountMarketBased == Decimal("50.0000")

    # Double the activity and re-save — all figures must double.
    rec.QuantityOrCost = Decimal("200")
    rec.save()
    rec.refresh_from_db()
    assert rec.EmissionsAmount == Decimal("100.0000")
    assert rec.EmissionsAmountLocationBased == Decimal("100.0000")
    assert rec.EmissionsAmountMarketBased == Decimal("100.0000")


def test_biogenic_co2_computed_and_excluded_from_total(entity, gwp_dataset):
    """Biogenic CO2 is reported separately and NOT folded into EmissionsAmount."""
    rec = _emission(
        entity, gwp_dataset, Scope=1,
        EmissionFactor=Decimal("2.0"), BiogenicCO2FactorKg=Decimal("0.3"),
    )
    # Fossil total: 1000 × 2.0 × GWP(CO2=1) = 2000 kg
    assert rec.EmissionsAmount == Decimal("2000.0000")
    # Biogenic: 1000 × 0.3 = 300 kg → 0.3 t, stored separately
    assert rec.BiogenicCO2AmountTonnes == Decimal("0.300000")


def test_no_biogenic_factor_leaves_field_null(entity, gwp_dataset):
    rec = _emission(entity, gwp_dataset, Scope=1)
    assert rec.BiogenicCO2AmountTonnes is None

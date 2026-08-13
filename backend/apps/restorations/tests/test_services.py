"""
Unit tests for the LULUCF carbon service (apps/restorations/services.py):
IPCC Tier-1 biomass carbon-stock loss for tree removals, and restoration
sequestration. These cover the formula and the parent-total aggregation
performed on save().
"""
from datetime import date
from decimal import Decimal

import pytest

pytestmark = pytest.mark.django_db


def _species(entity, **kwargs):
    from apps.ecosystem.models import Species
    defaults = dict(EntityId=entity.EntityId, CommonName="Test Tree")
    defaults.update(kwargs)
    return Species.objects.create(**defaults)


# ── Tree-removal biomass (IPCC Tier 1, volume-based) ────────────────────────────

def test_removed_species_carbon_tier1_volume(entity):
    """AGB = V·D·BEF; BGB = AGB·R; C = (AGB+BGB)·CF; CO2e = C·44/12."""
    from apps.restorations.models import TreeRemovalRemovedSpecies, TreeRemovals

    species = _species(
        entity, IPCCForestType="tropical",
        BasicWoodDensity=Decimal("0.6"), BiomassExpansionFactor=Decimal("1.74"),
        RootToShootRatio=Decimal("0.37"), CarbonFraction=Decimal("0.47"),
    )
    removal = TreeRemovals.objects.create(EntityId=entity)

    rs = TreeRemovalRemovedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=species, Count=1, VolumeM3=Decimal("10"),
    )

    # 10·0.6·1.74 = 10.44 ; ·0.37 = 3.8628 ; total 14.3028 ; ·0.47 = 6.722316 ; ·44/12 = 24.648492
    assert rs.AboveGroundBiomassTonnes == Decimal("10.4400")
    assert rs.BelowGroundBiomassTonnes == Decimal("3.8628")
    assert rs.CarbonStockTonnesC == Decimal("6.7223")
    assert rs.CO2EquivalentTonnes == Decimal("24.6485")
    assert rs.TotalCarbonStockLossTonnesCO2e == Decimal("24.6485")


def test_tree_removal_total_aggregates_on_save(entity):
    """TreeRemovals.TotalBiomassCarbon is the server-side sum of its removed species."""
    from apps.restorations.models import TreeRemovalRemovedSpecies, TreeRemovals

    species = _species(
        entity, IPCCForestType="tropical",
        BasicWoodDensity=Decimal("0.6"), BiomassExpansionFactor=Decimal("1.74"),
        RootToShootRatio=Decimal("0.37"), CarbonFraction=Decimal("0.47"),
    )
    removal = TreeRemovals.objects.create(EntityId=entity)
    TreeRemovalRemovedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=species, VolumeM3=Decimal("10"))
    TreeRemovalRemovedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=species, VolumeM3=Decimal("10"))

    removal.refresh_from_db()
    assert removal.TotalBiomassCarbon == Decimal("49.2970")  # 2 × 24.6485


def test_removed_species_no_volume_leaves_outputs_null(entity):
    from apps.restorations.models import TreeRemovalRemovedSpecies, TreeRemovals

    species = _species(entity, IPCCForestType="tropical")
    removal = TreeRemovals.objects.create(EntityId=entity)
    rs = TreeRemovalRemovedSpecies.objects.create(
        TreeRemovalId=removal, SpeciesId=species, Count=5)  # no VolumeM3

    assert rs.CO2EquivalentTonnes is None
    removal.refresh_from_db()
    assert removal.TotalBiomassCarbon == Decimal("0.0000")


# ── Restoration sequestration ───────────────────────────────────────────────────

def test_restoration_sequestration_formula(entity):
    """Cumulative = rate·area·years·survival·(1−leakage/100); survival defaults to 0.85."""
    from apps.restorations.models import Restorations, RestorationSpecies

    species = _species(entity, AnnualSequestrationRateTonnesCO2ePerHa=Decimal("10"))
    restoration = Restorations.objects.create(
        EntityId=entity, RestorationName="R1", StartDate=date(2022, 1, 1))

    rsp = RestorationSpecies.objects.create(
        RestorationId=restoration, SpeciesId=species, AreaHectares=Decimal("2"))

    # Years is derived from StartDate→today, so assert the formula against the stored value.
    assert rsp.YearsEstablished is not None and rsp.YearsEstablished > 0
    expected = (Decimal("10") * Decimal("2") * rsp.YearsEstablished
                * Decimal("0.85")).quantize(Decimal("0.0001"))
    assert rsp.CumulativeSequestrationTonnesCO2e == expected

    restoration.refresh_from_db()
    assert restoration.EstimatedCarbonSequestrationTonnes == expected


def test_restoration_leakage_discount_applied(entity):
    from apps.restorations.models import Restorations, RestorationSpecies

    species = _species(entity, AnnualSequestrationRateTonnesCO2ePerHa=Decimal("10"))
    restoration = Restorations.objects.create(
        EntityId=entity, RestorationName="R2", StartDate=date(2022, 1, 1))

    rsp = RestorationSpecies.objects.create(
        RestorationId=restoration, SpeciesId=species,
        AreaHectares=Decimal("2"), LeakageDiscountPercent=Decimal("20"),
    )

    gross = Decimal("10") * Decimal("2") * rsp.YearsEstablished * Decimal("0.85")
    expected = (gross * Decimal("0.8")).quantize(Decimal("0.0001"))  # 1 − 20/100
    assert rsp.CumulativeSequestrationTonnesCO2e == expected

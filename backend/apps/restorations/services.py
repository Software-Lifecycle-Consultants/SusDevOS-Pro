"""
LULUCF carbon service layer for tree removals and restorations.

Implements the IPCC biomass carbon-stock-change method (ghg_calculation_spec §6)
and restoration sequestration (§7). All carbon figures are server-populated here;
client-submitted values are overwritten (critical rule: never trust client carbon).

These figures are biogenic / LULUCF — reported as memo items, NOT folded into
GHG Protocol Scope 1/2/3 totals.
"""
from datetime import date
from decimal import Decimal

CO2_C_RATIO = Decimal("44") / Decimal("12")  # 3.6667 — molecular weight CO2/C
DEFAULT_CARBON_FRACTION = Decimal("0.47")     # IPCC default CF for all forest types

# IPCC Tier 1 defaults by forest type (used when Species params are not set).
# BEF: Table 4.5; R: Table 4.4; D: Table 4.13 (representative mid-values).
IPCC_DEFAULTS = {
    "tropical":  {"BEF": Decimal("1.74"), "R": Decimal("0.37"), "D": Decimal("0.60")},
    "temperate": {"BEF": Decimal("1.30"), "R": Decimal("0.26"), "D": Decimal("0.52")},
    "boreal":    {"BEF": Decimal("1.30"), "R": Decimal("0.23"), "D": Decimal("0.45")},
    "mangrove":  {"BEF": Decimal("1.74"), "R": Decimal("0.37"), "D": Decimal("0.60")},
    "savanna":   {"BEF": Decimal("1.40"), "R": Decimal("0.28"), "D": Decimal("0.55")},
    "shrubland": {"BEF": Decimal("1.40"), "R": Decimal("0.28"), "D": Decimal("0.50")},
    "grassland": {"BEF": Decimal("1.30"), "R": Decimal("0.26"), "D": Decimal("0.50")},
}


def _d(value) -> Decimal:
    return Decimal(str(value)) if value is not None else None


def _param(species, attr, forest_default_key):
    """Resolve a biomass parameter: species value first, then IPCC forest-type default."""
    val = getattr(species, attr, None)
    if val is not None:
        return _d(val)
    defaults = IPCC_DEFAULTS.get(getattr(species, "IPCCForestType", None) or "")
    return defaults.get(forest_default_key) if defaults else None


# ── Tree removals — carbon stock loss ───────────────────────────────────────────

def compute_removed_species_carbon(instance) -> None:
    """
    Populate AGB/BGB/total biomass/carbon stock/CO2e for one removed-species row.
    Mutates the instance in place; caller saves.

    Tier 1 (volume-based): AGB = VolumeM3 × D × BEF, BGB = AGB × R,
        Total = (AGB + BGB) × Count? — VolumeM3 is a per-removal total, so Count is
        NOT re-multiplied here (the volume already covers all trees of this species).
    Tier 4 (manual): values supplied directly; only the LULUCF total is summed.
    """
    method = instance.BiomassCalculationMethod

    # Tier 4 — values entered directly; do not overwrite, just roll up the total.
    if method == 4:
        instance.TotalCarbonStockLossTonnesCO2e = _sum_lulucf(instance)
        return

    species = instance.SpeciesId
    volume = _d(instance.VolumeM3)
    if species is None or volume is None:
        # Not enough data to compute — leave outputs null.
        instance.AboveGroundBiomassTonnes = None
        instance.BelowGroundBiomassTonnes = None
        instance.TotalBiomassTonnes = None
        instance.CarbonStockTonnesC = None
        instance.CO2EquivalentTonnes = None
        instance.TotalCarbonStockLossTonnesCO2e = _sum_lulucf(instance)
        return

    density = _param(species, "BasicWoodDensity", "D")
    bef = _param(species, "BiomassExpansionFactor", "BEF")
    root_shoot = _param(species, "RootToShootRatio", "R")
    cf = _d(species.CarbonFraction) or DEFAULT_CARBON_FRACTION

    if density is None or bef is None or root_shoot is None:
        instance.TotalCarbonStockLossTonnesCO2e = _sum_lulucf(instance)
        return

    agb = volume * density * bef
    bgb = agb * root_shoot
    total_biomass = agb + bgb
    carbon_stock = total_biomass * cf
    co2e = carbon_stock * CO2_C_RATIO

    instance.AboveGroundBiomassTonnes = agb.quantize(Decimal("0.0001"))
    instance.BelowGroundBiomassTonnes = bgb.quantize(Decimal("0.0001"))
    instance.TotalBiomassTonnes = total_biomass.quantize(Decimal("0.0001"))
    instance.CarbonStockTonnesC = carbon_stock.quantize(Decimal("0.0001"))
    instance.CO2EquivalentTonnes = co2e.quantize(Decimal("0.0001"))
    instance.TotalCarbonStockLossTonnesCO2e = _sum_lulucf(instance, co2e=co2e)


def _sum_lulucf(instance, co2e=None) -> Decimal:
    """CO2e + dead organic matter + soil carbon (the latter two optional, Tier 2/3)."""
    living = co2e if co2e is not None else (_d(instance.CO2EquivalentTonnes) or Decimal("0"))
    dom = _d(instance.DeadOrganicMatterTonnesCO2e) or Decimal("0")
    soil = _d(instance.SoilCarbonTonnesCO2e) or Decimal("0")
    return (living + dom + soil).quantize(Decimal("0.0001"))


def recompute_tree_removal_total(tree_removal) -> None:
    """Aggregate removed-species CO2e into TreeRemovals.TotalBiomassCarbon (server-only)."""
    from django.db.models import Sum
    total = tree_removal.removed_species.aggregate(
        t=Sum("TotalCarbonStockLossTonnesCO2e")
    )["t"] or Decimal("0")
    tree_removal.TotalBiomassCarbon = Decimal(str(total)).quantize(Decimal("0.0001"))
    tree_removal.save(update_fields=["TotalBiomassCarbon"])


# ── Restoration — sequestration ─────────────────────────────────────────────────

def compute_restoration_species_sequestration(instance) -> None:
    """
    CumulativeSequestrationTonnesCO2e =
        AnnualRate × AreaHa × YearsEstablished × SurvivalEstimate × (1 − Leakage/100)
    Mutates instance in place; caller saves.
    """
    rate = _d(instance.AnnualSequestrationRateTonnesCO2ePerHa)
    if rate is None and instance.SpeciesId is not None:
        rate = _d(instance.SpeciesId.AnnualSequestrationRateTonnesCO2ePerHa)
    area = _d(instance.AreaHectares)

    years = _years_established(instance)
    instance.YearsEstablished = years

    if rate is None or area is None or years is None:
        instance.CumulativeSequestrationTonnesCO2e = None
        return

    survival = _d(instance.SurvivalEstimate)
    if survival is None:
        survival = Decimal("0.85")
    leakage = _d(instance.LeakageDiscountPercent) or Decimal("0")

    gross = rate * area * years * survival
    net = gross * (Decimal("1") - leakage / Decimal("100"))
    instance.CumulativeSequestrationTonnesCO2e = net.quantize(Decimal("0.0001"))


def _years_established(instance):
    """Years from the parent restoration's StartDate to today (decimal, for audit)."""
    restoration = instance.RestorationId
    start = getattr(restoration, "StartDate", None)
    if not start:
        return None
    days = (date.today() - start).days
    if days < 0:
        return Decimal("0")
    return (Decimal(days) / Decimal("365.25")).quantize(Decimal("0.01"))


def recompute_restoration_total(restoration) -> None:
    """Aggregate species sequestration into Restorations.EstimatedCarbonSequestrationTonnes."""
    from django.db.models import Sum
    total = restoration.restoration_species.aggregate(
        t=Sum("CumulativeSequestrationTonnesCO2e")
    )["t"] or Decimal("0")
    restoration.EstimatedCarbonSequestrationTonnes = Decimal(str(total)).quantize(Decimal("0.0001"))
    restoration.save(update_fields=["EstimatedCarbonSequestrationTonnes"])

"""
Ecosystem app models: Ecosystem types and Species records.

SpeciesLandParcels uses IntegerField for LandParcelId to avoid a circular
dependency between ecosystem and land apps (documented in spec/app_structure.md).
"""
from django.db import models
from apps.shared.models import BaseAuditMixin

IUCN_STATUS_CHOICES = [
    ("LC", "Least Concern"), ("NT", "Near Threatened"), ("VU", "Vulnerable"),
    ("EN", "Endangered"), ("CR", "Critically Endangered"),
    ("EW", "Extinct in the Wild"), ("EX", "Extinct"),
    ("DD", "Data Deficient"), ("NE", "Not Evaluated"),
]

IPCC_FOREST_TYPE_CHOICES = [
    ("tropical", "Tropical"), ("temperate", "Temperate"), ("boreal", "Boreal"),
    ("mangrove", "Mangrove"), ("savanna", "Savanna / Woodland"),
    ("shrubland", "Shrubland"), ("grassland", "Grassland"),
]


class Ecosystem(BaseAuditMixin):
    EcosystemId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField(help_text="FK to entities.Entities")
    EcosystemName = models.CharField(max_length=200)
    EcosystemType = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    AreaHectares = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "ecosystem"
        ordering = ["EcosystemName"]

    def __str__(self):
        return self.EcosystemName


class EcosystemTags(models.Model):
    id = models.AutoField(primary_key=True)
    EcosystemId = models.ForeignKey(Ecosystem, on_delete=models.CASCADE, related_name="ecosystem_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="ecosystem_links")

    class Meta:
        db_table = "ecosystem_tags"


class Species(BaseAuditMixin):
    SpeciesId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField(help_text="FK to entities.Entities")
    CommonName = models.CharField(max_length=200)
    ScientificName = models.CharField(max_length=200, null=True, blank=True)
    Family = models.CharField(max_length=100, null=True, blank=True)
    Kingdom = models.CharField(max_length=50, null=True, blank=True)
    Description = models.TextField(blank=True, null=True)
    IUCNStatus = models.CharField(max_length=2, choices=IUCN_STATUS_CHOICES, null=True, blank=True)
    IUCNSyncedAt = models.DateTimeField(null=True, blank=True)
    GBIFKey = models.PositiveIntegerField(null=True, blank=True)
    # ── IPCC LULUCF biomass parameters (ghg_calculation_spec §6) ────────────────
    IPCCForestType = models.CharField(
        max_length=20, choices=IPCC_FOREST_TYPE_CHOICES, null=True, blank=True,
        help_text="IPCC forest type for Tier 1 BEF/R lookup",
    )
    BasicWoodDensity = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
        help_text="D — tonnes dry matter per m³ fresh volume (IPCC Table 4.13)",
    )
    BiomassExpansionFactor = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
        help_text="BEF — merchantable volume → total AGB (IPCC Table 4.5)",
    )
    RootToShootRatio = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True,
        help_text="R — below-ground/above-ground biomass ratio (IPCC Table 4.4)",
    )
    CarbonFraction = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True, default=0.47,
        help_text="CF — carbon content of dry biomass (IPCC default 0.47)",
    )
    AnnualSequestrationRateTonnesCO2ePerHa = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Mean annual CO2e sequestered per ha at maturity (IPCC Annex 3A.1)",
    )
    BiomassDataSource = models.CharField(
        max_length=200, null=True, blank=True,
        help_text="Citation for biomass parameter values (IPCC table ref, study DOI)",
    )

    class Meta:
        db_table = "species"
        ordering = ["CommonName"]
        indexes = [models.Index(fields=["GBIFKey"], name="idx_species_gbif_key")]

    def __str__(self):
        return self.CommonName


class SpeciesTags(models.Model):
    id = models.AutoField(primary_key=True)
    SpeciesId = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="species_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="species_links")

    class Meta:
        db_table = "species_tags"


class SpeciesLandParcels(models.Model):
    """Junction: Species <-> LandParcels. Uses IntegerField to avoid circular import."""
    id = models.AutoField(primary_key=True)
    SpeciesId = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="land_parcel_links")
    LandParcelId = models.IntegerField(help_text="FK to land.LandParcels (IntegerField — circular dep)")

    class Meta:
        db_table = "species_land_parcels"

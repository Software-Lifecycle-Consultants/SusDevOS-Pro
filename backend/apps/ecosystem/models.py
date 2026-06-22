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

"""Land app models: LandParcels and junction tables."""
from django.db import models

from apps.shared.models import BaseAuditMixin


class LandParcels(BaseAuditMixin):
    LandParcelId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="land_parcels")
    ParcelName = models.CharField(max_length=200)
    ParcelReference = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    AreaHectares = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    BoundaryGeoJSON = models.JSONField(null=True, blank=True, help_text="GeoJSON polygon boundary")
    Tenure = models.CharField(max_length=100, blank=True, null=True)
    LandUseType = models.CharField(max_length=100, blank=True, null=True)
    PlanningReference = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "land_parcels"
        ordering = ["ParcelName"]

    def __str__(self):
        return self.ParcelName


class LandParcelTags(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="land_parcel_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="land_parcel_links")

    class Meta:
        db_table = "land_parcel_tags"


class LandParcelEcosystems(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_ecosystems")
    EcosystemId = models.ForeignKey("ecosystem.Ecosystem", on_delete=models.CASCADE, related_name="land_parcel_links")

    class Meta:
        db_table = "land_parcel_ecosystems"


class LandParcelContacts(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_contacts")
    ContactId = models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="land_parcel_contacts")

    class Meta:
        db_table = "land_parcel_contacts"


class LandParcelDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_documents")
    DocumentId = models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="land_parcel_documents")

    class Meta:
        db_table = "land_parcel_documents"


class LandParcelImages(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_images")
    ImageId = models.ForeignKey("shared.Images", on_delete=models.CASCADE, related_name="land_parcel_images")

    class Meta:
        db_table = "land_parcel_images"


class LandParcelEntities(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_entities")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="parcel_entity_links")

    class Meta:
        db_table = "land_parcel_entities"


class LandParcelLocations(models.Model):
    id = models.AutoField(primary_key=True)
    LandParcelId = models.ForeignKey(LandParcels, on_delete=models.CASCADE, related_name="parcel_locations")
    LocationId = models.ForeignKey("shared.Locations", on_delete=models.CASCADE, related_name="land_parcel_locations")

    class Meta:
        db_table = "land_parcel_locations"

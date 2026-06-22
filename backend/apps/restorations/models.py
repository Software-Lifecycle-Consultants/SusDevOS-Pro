"""Restorations app models: TreeRemovals and Restorations with their junction tables."""
from django.db import models
from apps.shared.models import BaseAuditMixin


class TreeRemovals(BaseAuditMixin):
    TreeRemovalId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="tree_removals")
    ProjectId = models.ForeignKey(
        "projects.DevelopmentProjects", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tree_removals",
    )
    RemovalReference = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    RemovalDate = models.DateField(null=True, blank=True)
    TotalTreesRemoved = models.PositiveIntegerField(null=True, blank=True)
    TotalBiomassCarbon = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    HasMitigationPlan = models.BooleanField(default=False)
    MitigationNotes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tree_removals"
        ordering = ["-CreatedAt"]

    def __str__(self):
        return f"TreeRemoval {self.TreeRemovalId}"


class TreeRemovalEcosystems(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_ecosystems")
    EcosystemId = models.ForeignKey("ecosystem.Ecosystem", on_delete=models.CASCADE, related_name="tree_removal_links")

    class Meta:
        db_table = "tree_removal_ecosystems"


class TreeRemovalTags(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="tree_removal_links")

    class Meta:
        db_table = "tree_removal_tags"


class TreeRemovalContacts(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_contacts")
    ContactId = models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="tree_removal_contacts")

    class Meta:
        db_table = "tree_removal_contacts"


class TreeRemovalDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_documents")
    DocumentId = models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="tree_removal_documents")

    class Meta:
        db_table = "tree_removal_documents"


class TreeRemovalLandParcels(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_land_parcels")
    LandParcelId = models.ForeignKey("land.LandParcels", on_delete=models.CASCADE, related_name="tree_removal_links")

    class Meta:
        db_table = "tree_removal_land_parcels"


class TreeRemovalEntities(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_entities")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="tree_removal_entity_links")

    class Meta:
        db_table = "tree_removal_entities"


class TreeRemovalImages(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removal_images")
    ImageId = models.ForeignKey("shared.Images", on_delete=models.CASCADE, related_name="tree_removal_images")

    class Meta:
        db_table = "tree_removal_images"


class TreeRemovalRemovedSpecies(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="removed_species")
    SpeciesId = models.ForeignKey("ecosystem.Species", on_delete=models.CASCADE, related_name="tree_removal_removals")
    Count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "tree_removal_removed_species"


class TreeRemovalAffectedSpecies(models.Model):
    id = models.AutoField(primary_key=True)
    TreeRemovalId = models.ForeignKey(TreeRemovals, on_delete=models.CASCADE, related_name="affected_species")
    SpeciesId = models.ForeignKey("ecosystem.Species", on_delete=models.CASCADE, related_name="tree_removal_affected")
    Notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tree_removal_affected_species"


class Restorations(BaseAuditMixin):
    RestorationId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="restorations")
    RestorationName = models.CharField(max_length=200)
    RestorationReference = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    StartDate = models.DateField(null=True, blank=True)
    CompletionDate = models.DateField(null=True, blank=True)
    TotalAreaHectares = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    TotalTreesPlanted = models.PositiveIntegerField(null=True, blank=True)
    EstimatedCarbonSequestrationTonnes = models.DecimalField(
        max_digits=14, decimal_places=4, null=True, blank=True
    )
    MonitoringNotes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "restorations"
        ordering = ["RestorationName"]

    def __str__(self):
        return self.RestorationName


class RestorationEcosystems(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_ecosystems")
    EcosystemId = models.ForeignKey("ecosystem.Ecosystem", on_delete=models.CASCADE, related_name="restoration_links")

    class Meta:
        db_table = "restoration_ecosystems"


class RestorationTags(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="restoration_links")

    class Meta:
        db_table = "restoration_tags"


class RestorationDevelopmentProjects(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_projects")
    ProjectId = models.ForeignKey("projects.DevelopmentProjects", on_delete=models.CASCADE, related_name="restoration_links")

    class Meta:
        db_table = "restoration_development_projects"


class RestorationEntities(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_entities")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="restoration_entity_links")

    class Meta:
        db_table = "restoration_entities"


class RestorationSpecies(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_species")
    SpeciesId = models.ForeignKey("ecosystem.Species", on_delete=models.CASCADE, related_name="restoration_links")
    Count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "restoration_species"


class RestorationLandParcels(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_land_parcels")
    LandParcelId = models.ForeignKey("land.LandParcels", on_delete=models.CASCADE, related_name="restoration_links")

    class Meta:
        db_table = "restoration_land_parcels"


class RestorationLocations(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_locations")
    LocationId = models.ForeignKey("shared.Locations", on_delete=models.CASCADE, related_name="restoration_links")

    class Meta:
        db_table = "restoration_locations"


class RestorationContacts(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_contacts")
    ContactId = models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="restoration_contacts")

    class Meta:
        db_table = "restoration_contacts"


class RestorationDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_documents")
    DocumentId = models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="restoration_documents")

    class Meta:
        db_table = "restoration_documents"


class RestorationImages(models.Model):
    id = models.AutoField(primary_key=True)
    RestorationId = models.ForeignKey(Restorations, on_delete=models.CASCADE, related_name="restoration_images")
    ImageId = models.ForeignKey("shared.Images", on_delete=models.CASCADE, related_name="restoration_images")

    class Meta:
        db_table = "restoration_images"

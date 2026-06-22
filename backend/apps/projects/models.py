"""Projects app models: DevelopmentProjects, ProjectPhases, RelatedProjects, and junctions."""
from django.db import models
from apps.shared.models import BaseAuditMixin

CONSOLIDATION_APPROACH_CHOICES = [
    (1, "Equity Share"), (2, "Financial Control"), (3, "Operational Control"),
]


class DevelopmentProjects(BaseAuditMixin):
    ProjectId = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="projects")
    ProjectName = models.CharField(max_length=200)
    ProjectReference = models.CharField(max_length=100, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    ProjectType = models.CharField(max_length=100, blank=True, null=True)
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    Location = models.CharField(max_length=200, blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)
    TotalAreaHectares = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    EstimatedValueGBP = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "development_projects"
        ordering = ["-CreatedAt"]
        indexes = [models.Index(fields=["EntityId", "Status"], name="idx_project_entity_status")]

    def __str__(self):
        return self.ProjectName


class ProjectPhases(BaseAuditMixin):
    PhaseId = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="phases")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.PROTECT, related_name="project_phases")
    PhaseName = models.CharField(max_length=200)
    PhaseNumber = models.PositiveSmallIntegerField(null=True, blank=True)
    Description = models.TextField(blank=True, null=True)
    StartDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    TargetEmissionsTonnes = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "project_phases"
        ordering = ["PhaseNumber"]

    def __str__(self):
        return f"{self.ProjectId} - {self.PhaseName}"


class RelatedProjects(models.Model):
    id = models.AutoField(primary_key=True)
    PrimaryProjectId = models.ForeignKey(
        DevelopmentProjects, on_delete=models.CASCADE, related_name="related_as_primary"
    )
    RelatedProjectId = models.ForeignKey(
        DevelopmentProjects, on_delete=models.CASCADE, related_name="related_as_secondary"
    )
    RelationshipType = models.CharField(max_length=50, blank=True, null=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "related_projects"
        constraints = [
            models.UniqueConstraint(
                fields=["PrimaryProjectId", "RelatedProjectId"], name="unique_project_relation"
            )
        ]


class DevelopmentProjectTags(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="project_links")

    class Meta:
        db_table = "development_project_tags"


class DevelopmentProjectPartners(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_partners")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="partner_projects")
    PartnerSharePercent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    PartnerConsolidationApproach = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=CONSOLIDATION_APPROACH_CHOICES
    )
    IsDoubleCountingRisk = models.BooleanField(default=False)
    DoubleCountingNotes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "development_project_partners"
        indexes = [
            models.Index(fields=["EntityId", "ProjectId"], name="idx_project_partner_entity")
        ]


class DevelopmentProjectLandParcels(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_land_parcels")
    LandParcelId = models.ForeignKey("land.LandParcels", on_delete=models.CASCADE, related_name="project_links")

    class Meta:
        db_table = "development_project_land_parcels"


class DevelopmentProjectContacts(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_contacts")
    ContactId = models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="project_contacts")

    class Meta:
        db_table = "development_project_contacts"


class DevelopmentProjectDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_documents")
    DocumentId = models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="project_documents")

    class Meta:
        db_table = "development_project_documents"


class DevelopmentProjectImages(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_images")
    ImageId = models.ForeignKey("shared.Images", on_delete=models.CASCADE, related_name="project_images")

    class Meta:
        db_table = "development_project_images"


class DevelopmentProjectEntities(models.Model):
    id = models.AutoField(primary_key=True)
    ProjectId = models.ForeignKey(DevelopmentProjects, on_delete=models.CASCADE, related_name="project_entities")
    EntityId = models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="project_entity_links")

    class Meta:
        db_table = "development_project_entities"

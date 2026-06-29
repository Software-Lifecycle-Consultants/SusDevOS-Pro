"""
Entities app models.

Reconstructed from: spec/app_structure.md, spec/api_integrations.md,
reference migrations 0026_entity_consolidation + 0027_api_integration_fields.
"""
from django.db import models

from apps.shared.models import BaseAuditMixin

ENTITY_TYPE_CHOICES = [
    (1, "Limited Company"),
    (2, "PLC"),
    (3, "LLP"),
    (4, "Partnership"),
    (5, "Sole Trader"),
    (6, "Charity"),
    (7, "Public Body"),
    (8, "Other"),
]

CONSOLIDATION_APPROACH_CHOICES = [
    (1, "Equity Share"),
    (2, "Financial Control"),
    (3, "Operational Control"),
]


class Entities(BaseAuditMixin):
    """Top-level organisational entity. All tenant-scoped data filters on EntityId."""

    EntityId = models.AutoField(primary_key=True)
    EntityName = models.CharField(max_length=200)
    EntityType = models.PositiveSmallIntegerField(choices=ENTITY_TYPE_CHOICES, null=True, blank=True)
    RegistrationNumber = models.CharField(max_length=50, blank=True, null=True)
    VATNumber = models.CharField(max_length=50, blank=True, null=True)

    # Address
    AddressLine1 = models.CharField(max_length=255, blank=True, null=True)
    AddressLine2 = models.CharField(max_length=255, blank=True, null=True)
    City = models.CharField(max_length=100, blank=True, null=True)
    PostCode = models.CharField(max_length=20, blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)

    # Reporting settings
    BaseCurrency = models.CharField(max_length=3, default="GBP")
    FiscalYearEndMonth = models.PositiveSmallIntegerField(
        default=3, help_text="Month number (1–12) when the entity's fiscal year ends"
    )
    ShareEmissionsWithPartners = models.BooleanField(default=False)

    # GHG Protocol organisational boundary (ref: 0026_entity_consolidation)
    ConsolidationApproach = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=CONSOLIDATION_APPROACH_CHOICES
    )
    ParentEntityId = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="subsidiaries",
    )
    OwnershipSharePercent = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True
    )

    # External registry IDs (ref: 0027_api_integration_fields)
    CompaniesHouseNumber = models.CharField(max_length=20, null=True, blank=True)
    SICCodes = models.JSONField(default=list, blank=True)
    IncorporationDate = models.DateField(null=True, blank=True)
    ExternalRegistryUrl = models.URLField(null=True, blank=True)

    class Meta:
        db_table = "entities"
        ordering = ["EntityName"]
        indexes = [models.Index(fields=["EntityName"], name="idx_entity_name")]

    def __str__(self):
        return self.EntityName


class RelatedEntities(models.Model):
    """Junction: entity ↔ entity (branch / group relationship)."""

    id = models.AutoField(primary_key=True)
    ParentEntityId = models.ForeignKey(
        Entities, on_delete=models.CASCADE, related_name="child_relations"
    )
    ChildEntityId = models.ForeignKey(
        Entities, on_delete=models.CASCADE, related_name="parent_relations"
    )
    RelationshipType = models.CharField(max_length=50, blank=True, null=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "related_entities"
        constraints = [
            models.UniqueConstraint(
                fields=["ParentEntityId", "ChildEntityId"],
                name="unique_entity_relation",
            )
        ]


class EntityLocations(models.Model):
    id = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="entity_locations")
    LocationId = models.ForeignKey("shared.Locations", on_delete=models.CASCADE, related_name="entity_locations")

    class Meta:
        db_table = "entity_locations"
        constraints = [
            models.UniqueConstraint(fields=["EntityId", "LocationId"], name="unique_entity_location")
        ]


class EntityContacts(models.Model):
    id = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="entity_contacts")
    ContactId = models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="entity_contacts")

    class Meta:
        db_table = "entity_contacts"


class EntityDocuments(models.Model):
    id = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="entity_documents")
    DocumentId = models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="entity_documents")

    class Meta:
        db_table = "entity_documents"


class EntityTags(models.Model):
    id = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="entity_tags")
    TagId = models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="entity_tag_links")

    class Meta:
        db_table = "entity_tags"


class EntityApiKeysIntermediary(models.Model):
    """Links EntityApiKeys records to the Entities that own them."""

    id = models.AutoField(primary_key=True)
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="api_key_links")
    ApiKeyId = models.ForeignKey("shared.EntityApiKeys", on_delete=models.CASCADE, related_name="entity_links")

    class Meta:
        db_table = "entity_api_keys_intermediary"


class EntityMembers(models.Model):
    """
    Grants a user access to an entity beyond their primary EntityId — the
    mechanism for multi-entity users (consultants, group admins) to switch
    tenant context via the X-Entity-ID header.

    Membership-only: it grants *access*; the user's existing global role applies
    within each entity (per-entity roles are intentionally out of scope for now).
    """
    id = models.AutoField(primary_key=True)
    UserId = models.ForeignKey("users.Users", on_delete=models.CASCADE, related_name="entity_memberships")
    EntityId = models.ForeignKey(Entities, on_delete=models.CASCADE, related_name="members")
    CreatedAt = models.DateTimeField(auto_now_add=True)
    CreatedBy = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "entity_members"
        constraints = [
            models.UniqueConstraint(fields=["UserId", "EntityId"], name="unique_user_entity_membership"),
        ]
        indexes = [models.Index(fields=["UserId"], name="idx_entity_member_user")]

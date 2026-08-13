"""
Shared lookup / attachment models + AuditLog + the project-wide audit mixin.

This app is the base of the dependency chain — the 8 lookup models have no FK
dependencies on other apps (EntityId stored as plain IntegerField). AuditLog
FKs to entities + users and is added in migration 0002.
"""
from django.conf import settings
from django.db import models

MODULE_KEY_CHOICES = [
    ("entity_management", "Entity Management"),
    ("projects", "Development Projects"),
    ("land_parcels", "Land Parcels"),
    ("ecosystem", "Ecosystem & Species"),
    ("tree_removals", "Tree Removals"),
    ("restorations", "Restorations"),
    ("emissions", "Emissions"),
    ("reports", "Reports"),
    ("blog", "Blog"),
]

ACTION_CHOICES = [
    ("Create", "Create"),
    ("Read_Sensitive", "Read Sensitive"),
    ("Update", "Update"),
    ("Delete", "Delete (Soft)"),
    ("Verify", "Verify Emissions Record"),
    ("Unlock_Verified", "Unlock Verified Record"),
    ("Login", "Login"),
    ("Logout", "Logout"),
    ("LoginFailed", "Login Failed"),
    ("AccessDenied", "Access Denied"),
    ("PasswordReset", "Password Reset"),
    ("TokenRevoked", "Token Revoked"),
    ("Export", "Data Export"),
    ("BulkImport", "Bulk Import"),
    ("ReportGenerated", "Report Generated"),
]


class BaseAuditMixin(models.Model):
    """Audit + soft-delete fields shared by every model in the system.

    Soft delete is performed by setting Status = 4 and DeletedAt — rows are
    not physically removed by application code.
    """

    Status = models.PositiveSmallIntegerField(
        default=1, help_text="1: Active, 2: Disabled, 3: Draft, 4: Deleted"
    )
    ApprovalStatus = models.PositiveSmallIntegerField(
        default=1, help_text="1: Active, 2: Rejected, 3: Pending"
    )
    DeletedAt = models.DateTimeField(null=True, blank=True)
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    CreatedBy = models.IntegerField(null=True, blank=True)
    UpdatedBy = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class Locations(BaseAuditMixin):
    """Global (not entity-scoped) location records."""

    LocationId = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=100)
    City = models.CharField(max_length=100)
    Country = models.CharField(max_length=100)
    Remarks = models.CharField(max_length=200, blank=True, null=True)
    GPSCoordinates = models.JSONField(
        default=dict,
        help_text="GeoJSON Point: { type: 'Point', coordinates: [lng, lat] }",
    )

    class Meta:
        db_table = "locations"
        indexes = [
            models.Index(fields=["City", "Country"], name="idx_location_city_country"),
        ]

    def __str__(self):
        return f"{self.Title} ({self.City}, {self.Country})"


class Tags(BaseAuditMixin):
    """Entity-scoped tags. TagNameNormalized maintained for case-insensitive dedup."""

    TagId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField(help_text="FK to entities.Entities (IntegerField — avoids circular import)")
    TagName = models.CharField(max_length=100)
    TagNameNormalized = models.CharField(max_length=100)

    class Meta:
        db_table = "tags"
        constraints = [
            models.UniqueConstraint(
                fields=["EntityId", "TagNameNormalized"], name="unique_tag_per_entity"
            ),
        ]

    def save(self, *args, **kwargs):
        self.TagNameNormalized = (self.TagName or "").strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.TagName


class Contacts(BaseAuditMixin):
    """Entity-scoped contact records, owned by a module."""

    ContactId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField(help_text="FK to entities.Entities (IntegerField — avoids circular import)")
    Name = models.CharField(max_length=200)
    Designation = models.CharField(max_length=200, blank=True, null=True)
    Email = models.EmailField(max_length=255, blank=True, null=True)
    PhoneNumber = models.CharField(max_length=20, blank=True, null=True)
    ModuleKey = models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)
    AddressTitle = models.CharField(max_length=200, blank=True, null=True)
    AddressLine1 = models.CharField(max_length=255, blank=True, null=True)
    AddressLine2 = models.CharField(max_length=255, blank=True, null=True)
    PostCode = models.CharField(max_length=20, blank=True, null=True)
    Country = models.CharField(max_length=100, blank=True, null=True)
    GPSCoordinates = models.JSONField(default=dict, blank=True)
    LocationId = models.ForeignKey(
        "shared.Locations", on_delete=models.SET_NULL, null=True, blank=True,
    )

    class Meta:
        db_table = "contacts"

    def __str__(self):
        return self.Name


class Documents(BaseAuditMixin):
    """Entity-scoped document attachments. DocPath stores the S3 key only."""

    DocumentId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    DocTitle = models.CharField(max_length=200)
    DocPath = models.TextField()
    DocType = models.CharField(max_length=50)
    Description = models.TextField(blank=True, null=True)
    Excerpt = models.TextField(blank=True, null=True)
    DocField = models.CharField(max_length=100, blank=True, null=True)
    ModuleKey = models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)

    class Meta:
        db_table = "documents"

    def __str__(self):
        return self.DocTitle


class DocumentTags(models.Model):
    """Junction: Documents ↔ Tags."""

    id = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        "shared.Documents", on_delete=models.CASCADE, related_name="document_tags"
    )
    TagId = models.ForeignKey(
        "shared.Tags", on_delete=models.CASCADE, related_name="tagged_documents"
    )

    class Meta:
        db_table = "document_tags"


class Images(BaseAuditMixin):
    """Entity-scoped image attachments. ImagePath stores the S3 key only."""

    ImageId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    ImagePath = models.TextField()
    AltText = models.CharField(max_length=255, blank=True, null=True)
    Description = models.TextField(blank=True, null=True)
    Priority = models.PositiveSmallIntegerField(blank=True, null=True)
    IsCover = models.BooleanField(default=False)
    CopyrightInfo = models.TextField(blank=True, null=True)
    ModuleKey = models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)

    class Meta:
        db_table = "images"

    def __str__(self):
        return self.AltText or f"Image {self.ImageId}"


class ImageTags(models.Model):
    """Junction: Images ↔ Tags."""

    id = models.AutoField(primary_key=True)
    ImageId = models.ForeignKey(
        "shared.Images", on_delete=models.CASCADE, related_name="image_tags"
    )
    TagId = models.ForeignKey(
        "shared.Tags", on_delete=models.CASCADE, related_name="tagged_images"
    )

    class Meta:
        db_table = "image_tags"


class EntityApiKeys(BaseAuditMixin):
    """Hashed API keys issued to an entity. The raw key is never stored."""

    ApiKeyId = models.AutoField(primary_key=True)
    EntityId = models.IntegerField()
    HashedApiKey = models.CharField(max_length=255)
    KeyPrefix = models.CharField(max_length=8)
    ExpiryDate = models.DateTimeField(blank=True, null=True)
    AuthorizedByFor = models.TextField(blank=True)
    TargetEntityId = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "entity_api_keys"

    def __str__(self):
        return f"{self.KeyPrefix}… (entity {self.EntityId})"


class AuditLog(models.Model):
    """
    Append-only security and change audit trail.
    Populated via Django signals and the audit_log() helper — never written
    to directly from business logic.
    Ref: backend/migrations/0016_audit_log_revised.py
    """

    LogId = models.BigAutoField(primary_key=True)
    EntityId = models.ForeignKey(
        "entities.Entities", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
    )
    ChangedBy = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_actions",
    )
    ChangedByUsername = models.CharField(max_length=100, blank=True, null=True)
    Action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    TableName = models.CharField(max_length=100, blank=True, null=True)
    RecordId = models.IntegerField(null=True, blank=True)
    Description = models.TextField(blank=True, null=True)
    OldValues = models.JSONField(null=True, blank=True)
    NewValues = models.JSONField(null=True, blank=True)
    IpAddress = models.CharField(max_length=45, blank=True, null=True)
    UserAgent = models.CharField(max_length=500, blank=True, null=True)
    ChangedOn = models.DateTimeField(auto_now_add=True)
    RetentionTier = models.PositiveSmallIntegerField(
        default=2,
        help_text="1: 30-day, 2: 1-year (login/session), 3: 7-year (CRUD/regulatory)",
    )

    class Meta:
        db_table = "audit_log"
        ordering = ["-ChangedOn"]
        indexes = [
            models.Index(fields=["EntityId", "ChangedOn"], name="idx_audit_entity_date"),
            models.Index(fields=["TableName", "RecordId"], name="idx_audit_table_record"),
            models.Index(fields=["ChangedBy", "ChangedOn"], name="idx_audit_user_date"),
            models.Index(fields=["Action", "ChangedOn"], name="idx_audit_action_date"),
            models.Index(fields=["RetentionTier", "ChangedOn"], name="idx_audit_retention"),
        ]

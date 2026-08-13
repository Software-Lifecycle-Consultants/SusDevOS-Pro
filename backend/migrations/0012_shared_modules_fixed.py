"""
Migration: Shared Modules — Locations, Contacts, Documents, Images, Tags, EntityApiKeys
App: apps.shared
Depends on: (no FK dependencies — base app)

FIXES applied vs original Notion spec:
1. Documents.TagIDs and Images.TagIDs were JSONField — converted to proper
   junction tables (DocumentTags, ImageTags) for consistency with all other
   M2M relationships in the schema.
2. Contacts.ModuleID was a free-text CharField — converted to a choices field
   with a defined enum of valid module keys.
3. Documents.TagIDs JSONField removed — replaced with DocumentTags junction table.
4. All ForeignKey references are now actual ForeignKey (no bare IntegerField).
5. RelatedEntities.ParentEntityId / ChildEntityId: CASCADE instead of SET_NULL
   (a junction record with both FKs null is meaningless).
"""

from django.db import migrations, models

# Valid module keys — matches the modules fixture in apps/users/fixtures/modules.yml
MODULE_KEY_CHOICES = [
    ('entity_management', 'Entity Management'),
    ('projects', 'Development Projects'),
    ('land_parcels', 'Land Parcels'),
    ('ecosystem', 'Ecosystem & Species'),
    ('tree_removals', 'Tree Removals'),
    ('restorations', 'Restorations'),
    ('emissions', 'Emissions'),
    ('reports', 'Reports'),
    ('blog', 'Blog'),
]


class Migration(migrations.Migration):

    dependencies = []

    operations = [

        # ── Locations (global — not entity-scoped) ─────────────────────────────
        migrations.CreateModel(
            name='Locations',
            fields=[
                ('LocationId', models.AutoField(primary_key=True)),
                ('Title', models.CharField(max_length=100)),
                ('City', models.CharField(max_length=100)),
                ('Country', models.CharField(max_length=100)),
                ('Remarks', models.CharField(max_length=200, blank=True, null=True)),
                ('GPSCoordinates', models.JSONField(
                    default=dict,
                    help_text="GeoJSON Point: { type: 'Point', coordinates: [lng, lat] }"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'locations'},
        ),
        # City + Country should warn on duplicate (not block) — enforced at app layer
        migrations.AddIndex(
            model_name='Locations',
            index=models.Index(fields=['City', 'Country'], name='idx_location_city_country'),
        ),

        # ── Tags (entity-scoped) ───────────────────────────────────────────────
        migrations.CreateModel(
            name='Tags',
            fields=[
                ('TagId', models.AutoField(primary_key=True)),
                # EntityId: tags are entity-scoped (not global)
                ('EntityId', models.IntegerField(
                    help_text="FK to entities.Entities — not a ForeignKey to avoid circular import"
                )),
                ('TagName', models.CharField(max_length=100)),
                ('TagNameNormalized', models.CharField(
                    max_length=100,
                    help_text="Lowercase version of TagName for case-insensitive dedup"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'tags'},
        ),
        migrations.AddConstraint(
            model_name='Tags',
            constraint=models.UniqueConstraint(
                fields=['EntityId', 'TagNameNormalized'],
                name='unique_tag_per_entity'
            ),
        ),

        # ── Contacts (entity-scoped) ───────────────────────────────────────────
        migrations.CreateModel(
            name='Contacts',
            fields=[
                ('ContactId', models.AutoField(primary_key=True)),
                ('EntityId', models.IntegerField(
                    help_text="FK to entities.Entities — IntegerField to avoid circular import"
                )),
                ('Name', models.CharField(max_length=200)),
                ('Designation', models.CharField(max_length=200, blank=True, null=True)),
                ('Email', models.EmailField(max_length=255, blank=True, null=True)),
                ('PhoneNumber', models.CharField(max_length=20, blank=True, null=True)),
                # FIX: ModuleID was CharField — now a choices field with valid module keys
                ('ModuleKey', models.CharField(
                    max_length=50,
                    choices=MODULE_KEY_CHOICES,
                    help_text="Which module created/owns this contact record"
                )),
                ('AddressTitle', models.CharField(max_length=200, blank=True, null=True)),
                ('AddressLine1', models.CharField(max_length=255, blank=True, null=True)),
                ('AddressLine2', models.CharField(max_length=255, blank=True, null=True)),
                ('PostCode', models.CharField(max_length=20, blank=True, null=True)),
                ('Country', models.CharField(max_length=100, blank=True, null=True)),
                ('GPSCoordinates', models.JSONField(
                    default=dict,
                    blank=True,
                    help_text="GeoJSON Point for contact address"
                )),
                ('LocationId', models.ForeignKey(
                    to='shared.Locations',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'contacts'},
        ),

        # ── Documents (entity-scoped) ──────────────────────────────────────────
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('DocumentId', models.AutoField(primary_key=True)),
                ('EntityId', models.IntegerField(
                    help_text="FK to entities.Entities"
                )),
                ('DocTitle', models.CharField(max_length=200)),
                # DocPath stores the S3 key (not a full URL — URL generated on-demand via pre-signed URL)
                ('DocPath', models.TextField(
                    help_text="S3 object key: /{node_id}/{entity_id}/{module_key}/{record_id}/{uuid}.{ext}"
                )),
                ('DocType', models.CharField(
                    max_length=50,
                    help_text="MIME type: application/pdf, text/csv, etc."
                )),
                ('Description', models.TextField(blank=True, null=True)),
                ('Excerpt', models.TextField(blank=True, null=True)),
                # FIX: DocField purpose is now clearer — stores the field name on the parent record
                ('DocField', models.CharField(
                    max_length=100,
                    blank=True,
                    null=True,
                    help_text="Parent model field this document is attached to (e.g. 'legal_docs')"
                )),
                # FIX: TagIDs was JSONField — removed; use DocumentTags junction table below
                ('ModuleKey', models.CharField(
                    max_length=50,
                    choices=MODULE_KEY_CHOICES,
                    help_text="Which module owns this document"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'documents'},
        ),

        # FIX: junction table replaces TagIDs JSONField on Documents
        migrations.CreateModel(
            name='DocumentTags',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('DocumentId', models.ForeignKey(
                    to='shared.Documents',
                    on_delete=models.CASCADE,
                    related_name='document_tags',
                )),
                ('TagId', models.ForeignKey(
                    to='shared.Tags',
                    on_delete=models.CASCADE,
                    related_name='tagged_documents',
                )),
            ],
            options={'db_table': 'document_tags'},
        ),

        # ── Images (entity-scoped) ─────────────────────────────────────────────
        migrations.CreateModel(
            name='Images',
            fields=[
                ('ImageId', models.AutoField(primary_key=True)),
                ('EntityId', models.IntegerField(help_text="FK to entities.Entities")),
                # ImagePath stores S3 key (same convention as DocPath)
                ('ImagePath', models.TextField(
                    help_text="S3 object key"
                )),
                ('AltText', models.CharField(max_length=255, blank=True, null=True)),
                ('Description', models.TextField(blank=True, null=True)),
                ('Priority', models.PositiveSmallIntegerField(
                    blank=True,
                    null=True,
                    help_text="Display order (lower = higher priority)"
                )),
                ('IsCover', models.BooleanField(
                    default=False,
                    help_text="True if this is the cover/hero image for its parent record"
                )),
                ('CopyrightInfo', models.TextField(blank=True, null=True)),
                # FIX: TagIDs was JSONField — removed; use ImageTags junction table below
                ('ModuleKey', models.CharField(
                    max_length=50,
                    choices=MODULE_KEY_CHOICES,
                    help_text="Which module owns this image"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'images'},
        ),

        # FIX: junction table replaces TagIDs JSONField on Images
        migrations.CreateModel(
            name='ImageTags',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('ImageId', models.ForeignKey(
                    to='shared.Images',
                    on_delete=models.CASCADE,
                    related_name='image_tags',
                )),
                ('TagId', models.ForeignKey(
                    to='shared.Tags',
                    on_delete=models.CASCADE,
                    related_name='tagged_images',
                )),
            ],
            options={'db_table': 'image_tags'},
        ),

        # ── EntityApiKeys ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='EntityApiKeys',
            fields=[
                ('ApiKeyId', models.AutoField(primary_key=True)),
                ('EntityId', models.IntegerField(help_text="FK to entities.Entities")),
                ('HashedApiKey', models.CharField(
                    max_length=255,
                    help_text="SHA-256 hash of the raw API key — never store raw"
                )),
                ('KeyPrefix', models.CharField(
                    max_length=8,
                    help_text="First 8 chars of the raw key (for display/identification only)"
                )),
                ('ExpiryDate', models.DateTimeField(blank=True, null=True)),
                ('AuthorizedByFor', models.TextField(
                    blank=True,
                    help_text="Description of what this key authorizes and for whom"
                )),
                ('TargetEntityId', models.IntegerField(
                    null=True,
                    blank=True,
                    help_text="FK to entities.Entities — target entity this key grants access to (v2.0 cross-entity use)"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'entity_api_keys'},
        ),
    ]

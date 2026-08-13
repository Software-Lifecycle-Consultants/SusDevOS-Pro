from django.db import migrations, models

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


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Locations",
            fields=[
                ("LocationId", models.AutoField(primary_key=True)),
                ("Title", models.CharField(max_length=100)),
                ("City", models.CharField(max_length=100)),
                ("Country", models.CharField(max_length=100)),
                ("Remarks", models.CharField(max_length=200, blank=True, null=True)),
                ("GPSCoordinates", models.JSONField(default=dict)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "locations"},
        ),
        migrations.AddIndex(
            model_name="Locations",
            index=models.Index(fields=["City", "Country"], name="idx_location_city_country"),
        ),
        migrations.CreateModel(
            name="Tags",
            fields=[
                ("TagId", models.AutoField(primary_key=True)),
                ("EntityId", models.IntegerField()),
                ("TagName", models.CharField(max_length=100)),
                ("TagNameNormalized", models.CharField(max_length=100)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "tags"},
        ),
        migrations.AddConstraint(
            model_name="Tags",
            constraint=models.UniqueConstraint(
                fields=["EntityId", "TagNameNormalized"], name="unique_tag_per_entity"
            ),
        ),
        migrations.CreateModel(
            name="Contacts",
            fields=[
                ("ContactId", models.AutoField(primary_key=True)),
                ("EntityId", models.IntegerField()),
                ("Name", models.CharField(max_length=200)),
                ("Designation", models.CharField(max_length=200, blank=True, null=True)),
                ("Email", models.EmailField(max_length=255, blank=True, null=True)),
                ("PhoneNumber", models.CharField(max_length=20, blank=True, null=True)),
                ("ModuleKey", models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)),
                ("AddressTitle", models.CharField(max_length=200, blank=True, null=True)),
                ("AddressLine1", models.CharField(max_length=255, blank=True, null=True)),
                ("AddressLine2", models.CharField(max_length=255, blank=True, null=True)),
                ("PostCode", models.CharField(max_length=20, blank=True, null=True)),
                ("Country", models.CharField(max_length=100, blank=True, null=True)),
                ("GPSCoordinates", models.JSONField(default=dict, blank=True)),
                (
                    "LocationId",
                    models.ForeignKey(
                        to="shared.Locations",
                        on_delete=models.SET_NULL,
                        null=True,
                        blank=True,
                    ),
                ),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "contacts"},
        ),
        migrations.CreateModel(
            name="Documents",
            fields=[
                ("DocumentId", models.AutoField(primary_key=True)),
                ("EntityId", models.IntegerField()),
                ("DocTitle", models.CharField(max_length=200)),
                ("DocPath", models.TextField()),
                ("DocType", models.CharField(max_length=50)),
                ("Description", models.TextField(blank=True, null=True)),
                ("Excerpt", models.TextField(blank=True, null=True)),
                ("DocField", models.CharField(max_length=100, blank=True, null=True)),
                ("ModuleKey", models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "documents"},
        ),
        migrations.CreateModel(
            name="DocumentTags",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                (
                    "DocumentId",
                    models.ForeignKey(
                        to="shared.Documents",
                        on_delete=models.CASCADE,
                        related_name="document_tags",
                    ),
                ),
                (
                    "TagId",
                    models.ForeignKey(
                        to="shared.Tags",
                        on_delete=models.CASCADE,
                        related_name="tagged_documents",
                    ),
                ),
            ],
            options={"db_table": "document_tags"},
        ),
        migrations.CreateModel(
            name="Images",
            fields=[
                ("ImageId", models.AutoField(primary_key=True)),
                ("EntityId", models.IntegerField()),
                ("ImagePath", models.TextField()),
                ("AltText", models.CharField(max_length=255, blank=True, null=True)),
                ("Description", models.TextField(blank=True, null=True)),
                ("Priority", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("IsCover", models.BooleanField(default=False)),
                ("CopyrightInfo", models.TextField(blank=True, null=True)),
                ("ModuleKey", models.CharField(max_length=50, choices=MODULE_KEY_CHOICES)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "images"},
        ),
        migrations.CreateModel(
            name="ImageTags",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                (
                    "ImageId",
                    models.ForeignKey(
                        to="shared.Images",
                        on_delete=models.CASCADE,
                        related_name="image_tags",
                    ),
                ),
                (
                    "TagId",
                    models.ForeignKey(
                        to="shared.Tags",
                        on_delete=models.CASCADE,
                        related_name="tagged_images",
                    ),
                ),
            ],
            options={"db_table": "image_tags"},
        ),
        migrations.CreateModel(
            name="EntityApiKeys",
            fields=[
                ("ApiKeyId", models.AutoField(primary_key=True)),
                ("EntityId", models.IntegerField()),
                ("HashedApiKey", models.CharField(max_length=255)),
                ("KeyPrefix", models.CharField(max_length=8)),
                ("ExpiryDate", models.DateTimeField(blank=True, null=True)),
                ("AuthorizedByFor", models.TextField(blank=True)),
                ("TargetEntityId", models.IntegerField(null=True, blank=True)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "entity_api_keys"},
        ),
    ]

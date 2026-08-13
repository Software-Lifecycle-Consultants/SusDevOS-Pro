from django.db import migrations, models

ENTITY_TYPE_CHOICES = [
    (1, "Limited Company"), (2, "PLC"), (3, "LLP"), (4, "Partnership"),
    (5, "Sole Trader"), (6, "Charity"), (7, "Public Body"), (8, "Other"),
]

CONSOLIDATION_APPROACH_CHOICES = [
    (1, "Equity Share"), (2, "Financial Control"), (3, "Operational Control"),
]


class Migration(migrations.Migration):

    initial = True
    dependencies = [("shared", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Entities",
            fields=[
                ("EntityId", models.AutoField(primary_key=True)),
                ("EntityName", models.CharField(max_length=200)),
                ("EntityType", models.PositiveSmallIntegerField(choices=ENTITY_TYPE_CHOICES, null=True, blank=True)),
                ("RegistrationNumber", models.CharField(max_length=50, blank=True, null=True)),
                ("VATNumber", models.CharField(max_length=50, blank=True, null=True)),
                ("AddressLine1", models.CharField(max_length=255, blank=True, null=True)),
                ("AddressLine2", models.CharField(max_length=255, blank=True, null=True)),
                ("City", models.CharField(max_length=100, blank=True, null=True)),
                ("PostCode", models.CharField(max_length=20, blank=True, null=True)),
                ("Country", models.CharField(max_length=100, blank=True, null=True)),
                ("BaseCurrency", models.CharField(max_length=3, default="GBP")),
                ("FiscalYearEndMonth", models.PositiveSmallIntegerField(default=3)),
                ("ShareEmissionsWithPartners", models.BooleanField(default=False)),
                ("ConsolidationApproach", models.PositiveSmallIntegerField(choices=CONSOLIDATION_APPROACH_CHOICES, null=True, blank=True)),
                ("ParentEntityId", models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subsidiaries")),
                ("OwnershipSharePercent", models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)),
                ("CompaniesHouseNumber", models.CharField(max_length=20, null=True, blank=True)),
                ("SICCodes", models.JSONField(default=list, blank=True)),
                ("IncorporationDate", models.DateField(null=True, blank=True)),
                ("ExternalRegistryUrl", models.URLField(null=True, blank=True)),
                ("Status", models.PositiveSmallIntegerField(default=1)),
                ("ApprovalStatus", models.PositiveSmallIntegerField(default=1)),
                ("DeletedAt", models.DateTimeField(null=True, blank=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
                ("UpdatedAt", models.DateTimeField(auto_now=True)),
                ("CreatedBy", models.IntegerField(null=True, blank=True)),
                ("UpdatedBy", models.IntegerField(null=True, blank=True)),
            ],
            options={"db_table": "entities"},
        ),
        migrations.AddIndex(
            model_name="Entities",
            index=models.Index(fields=["EntityName"], name="idx_entity_name"),
        ),
        migrations.CreateModel(
            name="RelatedEntities",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("ParentEntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="child_relations")),
                ("ChildEntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="parent_relations")),
                ("RelationshipType", models.CharField(max_length=50, blank=True, null=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "related_entities"},
        ),
        migrations.AddConstraint(
            model_name="RelatedEntities",
            constraint=models.UniqueConstraint(fields=["ParentEntityId", "ChildEntityId"], name="unique_entity_relation"),
        ),
        migrations.CreateModel(
            name="EntityLocations",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="entity_locations")),
                ("LocationId", models.ForeignKey("shared.Locations", on_delete=models.CASCADE, related_name="entity_locations")),
            ],
            options={"db_table": "entity_locations"},
        ),
        migrations.AddConstraint(
            model_name="EntityLocations",
            constraint=models.UniqueConstraint(fields=["EntityId", "LocationId"], name="unique_entity_location"),
        ),
        migrations.CreateModel(
            name="EntityContacts",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="entity_contacts")),
                ("ContactId", models.ForeignKey("shared.Contacts", on_delete=models.CASCADE, related_name="entity_contacts")),
            ],
            options={"db_table": "entity_contacts"},
        ),
        migrations.CreateModel(
            name="EntityDocuments",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="entity_documents")),
                ("DocumentId", models.ForeignKey("shared.Documents", on_delete=models.CASCADE, related_name="entity_documents")),
            ],
            options={"db_table": "entity_documents"},
        ),
        migrations.CreateModel(
            name="EntityTags",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="entity_tags")),
                ("TagId", models.ForeignKey("shared.Tags", on_delete=models.CASCADE, related_name="entity_tag_links")),
            ],
            options={"db_table": "entity_tags"},
        ),
        migrations.CreateModel(
            name="EntityApiKeysIntermediary",
            fields=[
                ("id", models.AutoField(primary_key=True)),
                ("EntityId", models.ForeignKey("entities.Entities", on_delete=models.CASCADE, related_name="api_key_links")),
                ("ApiKeyId", models.ForeignKey("shared.EntityApiKeys", on_delete=models.CASCADE, related_name="entity_links")),
            ],
            options={"db_table": "entity_api_keys_intermediary"},
        ),
    ]

from django.conf import settings
from django.db import migrations, models

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


class Migration(migrations.Migration):

    dependencies = [
        ("shared", "0001_initial"),
        ("entities", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("LogId", models.BigAutoField(primary_key=True)),
                ("EntityId", models.ForeignKey(
                    to="entities.Entities", on_delete=models.SET_NULL,
                    null=True, blank=True, related_name="audit_logs",
                )),
                ("ChangedBy", models.ForeignKey(
                    to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                    null=True, blank=True, related_name="audit_actions",
                )),
                ("ChangedByUsername", models.CharField(max_length=100, blank=True, null=True)),
                ("Action", models.CharField(max_length=50, choices=ACTION_CHOICES)),
                ("TableName", models.CharField(max_length=100, blank=True, null=True)),
                ("RecordId", models.IntegerField(null=True, blank=True)),
                ("Description", models.TextField(blank=True, null=True)),
                ("OldValues", models.JSONField(null=True, blank=True)),
                ("NewValues", models.JSONField(null=True, blank=True)),
                ("IpAddress", models.CharField(max_length=45, blank=True, null=True)),
                ("UserAgent", models.CharField(max_length=500, blank=True, null=True)),
                ("ChangedOn", models.DateTimeField(auto_now_add=True)),
                ("RetentionTier", models.PositiveSmallIntegerField(default=2)),
            ],
            options={"db_table": "audit_log", "ordering": ["-ChangedOn"]},
        ),
        migrations.AddIndex(
            model_name="AuditLog",
            index=models.Index(fields=["EntityId", "ChangedOn"], name="idx_audit_entity_date"),
        ),
        migrations.AddIndex(
            model_name="AuditLog",
            index=models.Index(fields=["TableName", "RecordId"], name="idx_audit_table_record"),
        ),
        migrations.AddIndex(
            model_name="AuditLog",
            index=models.Index(fields=["ChangedBy", "ChangedOn"], name="idx_audit_user_date"),
        ),
        migrations.AddIndex(
            model_name="AuditLog",
            index=models.Index(fields=["Action", "ChangedOn"], name="idx_audit_action_date"),
        ),
        migrations.AddIndex(
            model_name="AuditLog",
            index=models.Index(fields=["RetentionTier", "ChangedOn"], name="idx_audit_retention"),
        ),
    ]

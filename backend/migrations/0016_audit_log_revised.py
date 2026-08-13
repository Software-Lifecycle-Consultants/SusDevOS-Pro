"""
Migration: AuditLog (Revised)
App: apps.audit
Depends on: apps.entities, apps.users

REPLACES the original AuditLogs migration from the Notion spec.

Key changes vs original:
- Renamed to AuditLog (singular) for Django convention
- Added EntityId (tenant FK) — essential for filtering in multi-tenant context
- Added OldValues / NewValues JSON snapshots — actual change tracking
- Added IpAddress, UserAgent — security audit requirements
- Action field is now a defined choices field (not free-text VARCHAR)
- BIGINT primary key for high-volume write throughput
- Retention: 7 years for CRUD/emissions/user actions; 1 year for login;
  30 days for access-denied; 90 days for system errors.
  Enforced by Celery Beat task (apps/core/tasks.py: purge_expired_audit_logs)

This table is append-only — no UPDATE or DELETE via application code.
Rows are only removed by the scheduled retention purge task.

Population:
  - Via Django signals in each app (post_save, post_delete)
  - Via explicit audit_log() helper for non-model actions (login, access-denied)
  - Never written to directly from serializer/view logic
"""

from django.db import migrations, models

ACTION_CHOICES = [
    ('Create',          'Create'),
    ('Read_Sensitive',  'Read Sensitive'),   # e.g. viewing API keys
    ('Update',          'Update'),
    ('Delete',          'Delete (Soft)'),
    ('Verify',          'Verify Emissions Record'),
    ('Unlock_Verified', 'Unlock Verified Record'),
    ('Login',           'Login'),
    ('Logout',          'Logout'),
    ('LoginFailed',     'Login Failed'),
    ('AccessDenied',    'Access Denied'),
    ('PasswordReset',   'Password Reset'),
    ('TokenRevoked',    'Token Revoked'),
    ('Export',          'Data Export'),
    ('BulkImport',      'Bulk Import'),
    ('ReportGenerated', 'Report Generated'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                # BIGINT for high-volume logs
                ('LogId', models.BigAutoField(primary_key=True)),
                # EntityId is required for tenant-scoped filtering (Admins see own entity only)
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='audit_logs',
                    help_text="Tenant context — NULL only for SuperAdmin-level actions"
                )),
                ('ChangedBy', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='audit_actions',
                )),
                # Denormalised user info in case user is later soft-deleted
                ('ChangedByUsername', models.CharField(
                    max_length=100,
                    blank=True,
                    null=True,
                    help_text="Snapshot of username at time of action"
                )),
                ('Action', models.CharField(
                    max_length=50,
                    choices=ACTION_CHOICES,
                )),
                ('TableName', models.CharField(
                    max_length=100,
                    blank=True,
                    null=True,
                    help_text="DB table affected (e.g. 'emissions_data', 'users')"
                )),
                ('RecordId', models.IntegerField(
                    null=True,
                    blank=True,
                    help_text="PK of the affected record"
                )),
                ('Description', models.TextField(
                    blank=True,
                    null=True,
                    help_text="Human-readable summary of the action"
                )),
                # Change snapshots — NULL for non-data actions (login, access-denied)
                ('OldValues', models.JSONField(
                    null=True,
                    blank=True,
                    help_text="Snapshot of affected fields BEFORE the change"
                )),
                ('NewValues', models.JSONField(
                    null=True,
                    blank=True,
                    help_text="Snapshot of affected fields AFTER the change"
                )),
                # Security metadata
                ('IpAddress', models.CharField(
                    max_length=45,
                    blank=True,
                    null=True,
                    help_text="IPv6-compatible client IP"
                )),
                ('UserAgent', models.CharField(
                    max_length=500,
                    blank=True,
                    null=True,
                )),
                ('ChangedOn', models.DateTimeField(auto_now_add=True)),
                # Retention tier — used by cleanup task to apply correct retention period
                ('RetentionTier', models.PositiveSmallIntegerField(
                    default=2,
                    help_text=(
                        "1: 30-day (access-denied, high-volume), "
                        "2: 1-year (login/session), "
                        "3: 7-year (CRUD, emissions, user management — regulatory)"
                    )
                )),
            ],
            options={
                'db_table': 'audit_log',
                'ordering': ['-ChangedOn'],
            },
        ),
        migrations.AddIndex(
            model_name='AuditLog',
            index=models.Index(fields=['EntityId', 'ChangedOn'], name='idx_audit_entity_date'),
        ),
        migrations.AddIndex(
            model_name='AuditLog',
            index=models.Index(fields=['TableName', 'RecordId'], name='idx_audit_table_record'),
        ),
        migrations.AddIndex(
            model_name='AuditLog',
            index=models.Index(fields=['ChangedBy', 'ChangedOn'], name='idx_audit_user_date'),
        ),
        migrations.AddIndex(
            model_name='AuditLog',
            index=models.Index(fields=['Action', 'ChangedOn'], name='idx_audit_action_date'),
        ),
        migrations.AddIndex(
            model_name='AuditLog',
            index=models.Index(fields=['RetentionTier', 'ChangedOn'], name='idx_audit_retention'),
        ),
    ]

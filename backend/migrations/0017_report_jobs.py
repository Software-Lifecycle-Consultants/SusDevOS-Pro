"""
Migration: ReportJobs
App: apps.reports
Depends on: apps.entities, apps.users

Report generation is async via Celery. Requesting a report creates a ReportJob
record and returns its ID immediately (HTTP 202 Accepted). The frontend polls
GET /api/v1/reports/{id}/ until Status = Complete or Failed.

On completion, the generated file is uploaded to S3 at:
  /{node_id}/{entity_id}/reports/{uuid}.{ext}

A pre-signed download URL (24h expiry) is returned via
GET /api/v1/reports/{id}/download/

ReportJob rows are retained for 90 days then purged by Celery Beat task.
"""

from django.db import migrations, models

REPORT_TYPE_CHOICES = [
    ('emissions_summary', 'Project Emissions Summary'),
    ('ghg_inventory',     'Entity GHG Inventory'),
    ('phase_progress',    'Phase Progress vs Goals'),
    ('tree_log',          'Tree Removal & Restoration Log'),
]

REPORT_FORMAT_CHOICES = [
    ('pdf',  'PDF'),
    ('csv',  'CSV'),
    ('json', 'JSON'),
]

REPORT_STATUS_CHOICES = [
    (1, 'Queued'),
    (2, 'Processing'),
    (3, 'Complete'),
    (4, 'Failed'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportJobs',
            fields=[
                ('ReportJobId', models.AutoField(primary_key=True)),
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='report_jobs',
                )),
                ('RequestedBy', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name='report_jobs',
                )),
                ('ReportType', models.CharField(
                    max_length=50,
                    choices=REPORT_TYPE_CHOICES,
                )),
                ('Format', models.CharField(
                    max_length=10,
                    choices=REPORT_FORMAT_CHOICES,
                )),
                # Parameters passed to the report generator (flexible JSON)
                ('Parameters', models.JSONField(
                    default=dict,
                    help_text=(
                        "Report-specific parameters. Examples:\n"
                        "  emissions_summary: { projectId, reportingPeriodFrom, reportingPeriodTo }\n"
                        "  ghg_inventory: { entityId, baselineYear, reportingPeriodFrom, reportingPeriodTo }\n"
                        "  phase_progress: { projectId, phaseId }\n"
                        "  tree_log: { entityId, from, to }"
                    )
                )),
                ('JobStatus', models.PositiveSmallIntegerField(
                    default=1,
                    choices=REPORT_STATUS_CHOICES,
                )),
                ('CeleryTaskId', models.CharField(
                    max_length=255,
                    blank=True,
                    null=True,
                    help_text="Celery async_result task ID for status polling"
                )),
                # Output
                ('S3Key', models.TextField(
                    blank=True,
                    null=True,
                    help_text="S3 object key of the generated file — set on completion"
                )),
                ('FileSizeBytes', models.BigIntegerField(
                    null=True,
                    blank=True,
                )),
                ('ErrorMessage', models.TextField(
                    blank=True,
                    null=True,
                    help_text="Populated when JobStatus = Failed"
                )),
                ('QueuedAt', models.DateTimeField(auto_now_add=True)),
                ('StartedAt', models.DateTimeField(null=True, blank=True)),
                ('CompletedAt', models.DateTimeField(null=True, blank=True)),
                # Retention — purge after 90 days
                ('PurgeAfter', models.DateTimeField(
                    help_text="Set to QueuedAt + 90 days on create"
                )),
            ],
            options={
                'db_table': 'report_jobs',
                'ordering': ['-QueuedAt'],
            },
        ),
        migrations.AddIndex(
            model_name='ReportJobs',
            index=models.Index(fields=['EntityId', 'JobStatus'], name='idx_report_entity_status'),
        ),
        migrations.AddIndex(
            model_name='ReportJobs',
            index=models.Index(fields=['PurgeAfter'], name='idx_report_purge'),
        ),
    ]

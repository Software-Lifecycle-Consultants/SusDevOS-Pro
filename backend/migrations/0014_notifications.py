"""
Migration: Notifications
App: apps.notifications
Depends on: apps.entities, apps.users

In-app notifications polled every 60 seconds by the frontend.
Max 100 notifications per user — older ones pruned by Celery Beat task.
Email delivery for certain notification types is handled by Celery tasks
and does not go through this table.

NotificationType values must match the event keys defined in the Gaps & Resolutions
spec section 12.1. These are enforced as a choices field to prevent drift.
"""

from django.db import migrations, models

NOTIFICATION_TYPE_CHOICES = [
    ('user_created',          'New User Created'),
    ('emissions_submitted',   'Emissions Record Submitted'),
    ('emissions_verified',    'Emissions Record Verified'),
    ('emissions_unlocked',    'Verified Record Unlocked'),
    ('system_error',          'System Error (500)'),
    ('access_denied',         'Access Denied Attempt'),
    ('entity_created',        'New Entity Created'),
    ('password_reset',        'Password Reset Requested'),
    ('report_ready',          'Report Generation Complete'),
    ('report_failed',         'Report Generation Failed'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('NotificationId', models.AutoField(primary_key=True)),
                ('UserId', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.CASCADE,
                    related_name='notifications',
                    help_text="Recipient user"
                )),
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.CASCADE,
                    related_name='notifications',
                    help_text="Entity context for tenant isolation"
                )),
                ('Type', models.CharField(
                    max_length=50,
                    choices=NOTIFICATION_TYPE_CHOICES,
                )),
                ('Title', models.CharField(max_length=200)),
                ('Body', models.TextField()),
                # RelatedModule + RelatedRecordId allow the frontend to link
                # directly to the relevant record (e.g. click notification → open emissions record)
                ('RelatedModule', models.CharField(
                    max_length=50,
                    blank=True,
                    null=True,
                    help_text="Module key of the related record (e.g. 'emissions')"
                )),
                ('RelatedRecordId', models.IntegerField(
                    null=True,
                    blank=True,
                    help_text="PK of the related record in RelatedModule"
                )),
                ('IsRead', models.BooleanField(default=False)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'notifications'},
        ),
        migrations.AddIndex(
            model_name='Notifications',
            index=models.Index(
                fields=['UserId', 'IsRead', 'CreatedAt'],
                name='idx_notif_user_unread',
            ),
        ),
        migrations.AddIndex(
            model_name='Notifications',
            index=models.Index(
                fields=['EntityId'],
                name='idx_notif_entity',
            ),
        ),
    ]

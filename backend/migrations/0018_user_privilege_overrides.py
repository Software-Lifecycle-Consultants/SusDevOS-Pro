"""
Migration: UserPrivilegeOverrides
App: apps.users
Depends on: apps.users (Users, Interfaces)

This table was missing from the original migrations but is required by the
resolved privilege system (spec/privilege_system_resolved.md).

It stores per-user Grant/Revoke overrides that take precedence over the
role-based RolePrivileges. This allows exceptions (e.g. a Staff user with
temporary Verify Emissions access) without creating new roles.

See privilege resolution algorithm in spec/privilege_system_resolved.md.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_modules_interfaces_privileges'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPrivilegeOverrides',
            fields=[
                ('OverrideId', models.AutoField(primary_key=True)),
                ('UserId', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.CASCADE,
                    related_name='privilege_overrides',
                )),
                ('InterfaceId', models.ForeignKey(
                    to='users.Interfaces',
                    on_delete=models.CASCADE,
                    related_name='user_overrides',
                )),
                ('PermissionType', models.PositiveSmallIntegerField(
                    help_text="1: Create, 2: Read, 3: Update, 4: Delete, 5: All"
                )),
                ('OverrideAction', models.PositiveSmallIntegerField(
                    help_text="1: Grant (add this permission), 2: Revoke (remove this permission)"
                )),
                ('Reason', models.TextField(
                    blank=True,
                    null=True,
                    help_text="Mandatory explanation for the override (audit trail)"
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
            options={'db_table': 'user_privilege_overrides'},
        ),
        migrations.AddConstraint(
            model_name='UserPrivilegeOverrides',
            constraint=models.UniqueConstraint(
                fields=['UserId', 'InterfaceId', 'PermissionType'],
                name='unique_override_per_user_interface_permission'
            ),
        ),
    ]

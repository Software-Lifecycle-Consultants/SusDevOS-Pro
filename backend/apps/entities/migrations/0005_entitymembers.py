import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0004_drop_orphaned_sbti_column'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityMembers',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('CreatedBy', models.IntegerField(blank=True, null=True)),
                ('EntityId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='members', to='entities.entities')),
                ('UserId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='entity_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'entity_members'},
        ),
        migrations.AddConstraint(
            model_name='entitymembers',
            constraint=models.UniqueConstraint(fields=('UserId', 'EntityId'),
                name='unique_user_entity_membership'),
        ),
        migrations.AddIndex(
            model_name='entitymembers',
            index=models.Index(fields=['UserId'], name='idx_entity_member_user'),
        ),
    ]

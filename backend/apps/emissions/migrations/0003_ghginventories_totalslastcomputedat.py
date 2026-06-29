from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0002_alter_emissionfactors_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ghginventories',
            name='TotalsLastComputedAt',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='Timestamp of last scope-total recompute. NULL or >24h old => stale (see tasks.emissions).',
            ),
        ),
    ]

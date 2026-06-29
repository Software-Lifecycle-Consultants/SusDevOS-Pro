from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0004_emissionsdata_dual_scope2_biogenic'),
    ]

    operations = [
        migrations.AddField(
            model_name='emissionsoffsets',
            name='CreditRegistry',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                choices=[
                    ('verra', 'Verra (VCS)'),
                    ('gold_standard', 'Gold Standard'),
                    ('other', 'Other / Unlisted'),
                ],
                help_text='Which registry validates this credit (drives the registry-sync task).',
            ),
        ),
    ]

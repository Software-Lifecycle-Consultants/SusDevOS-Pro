from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0003_ghginventories_totalslastcomputedat'),
    ]

    operations = [
        migrations.AddField(
            model_name='emissionsdata',
            name='BiogenicCO2FactorKg',
            field=models.DecimalField(
                blank=True, null=True, max_digits=18, decimal_places=8,
                help_text='kg biogenic CO2 per canonical unit of fuel (combustion of biomass/biofuels).',
            ),
        ),
        migrations.AddField(
            model_name='emissionsdata',
            name='EFLocationBased',
            field=models.DecimalField(
                blank=True, null=True, max_digits=18, decimal_places=8,
                help_text='Grid-average emission factor (kg CO2e per canonical unit).',
            ),
        ),
        migrations.AddField(
            model_name='emissionsdata',
            name='EFMarketBased',
            field=models.DecimalField(
                blank=True, null=True, max_digits=18, decimal_places=8,
                help_text='Contractual/supplier emission factor (kg CO2e per canonical unit); 0 if 100% renewable EACs.',
            ),
        ),
    ]

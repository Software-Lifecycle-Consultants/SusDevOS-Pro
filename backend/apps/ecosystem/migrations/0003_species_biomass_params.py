from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ecosystem', '0002_alter_ecosystem_options_alter_species_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='IPCCForestType',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                choices=[
                    ('tropical', 'Tropical'), ('temperate', 'Temperate'),
                    ('boreal', 'Boreal'), ('mangrove', 'Mangrove'),
                    ('savanna', 'Savanna / Woodland'), ('shrubland', 'Shrubland'),
                    ('grassland', 'Grassland'),
                ],
                help_text='IPCC forest type for Tier 1 BEF/R lookup',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='BasicWoodDensity',
            field=models.DecimalField(
                blank=True, null=True, max_digits=8, decimal_places=4,
                help_text='D — tonnes dry matter per m³ fresh volume (IPCC Table 4.13)',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='BiomassExpansionFactor',
            field=models.DecimalField(
                blank=True, null=True, max_digits=8, decimal_places=4,
                help_text='BEF — merchantable volume → total AGB (IPCC Table 4.5)',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='RootToShootRatio',
            field=models.DecimalField(
                blank=True, null=True, max_digits=8, decimal_places=4,
                help_text='R — below-ground/above-ground biomass ratio (IPCC Table 4.4)',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='CarbonFraction',
            field=models.DecimalField(
                blank=True, null=True, max_digits=6, decimal_places=4, default=0.47,
                help_text='CF — carbon content of dry biomass (IPCC default 0.47)',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='AnnualSequestrationRateTonnesCO2ePerHa',
            field=models.DecimalField(
                blank=True, null=True, max_digits=10, decimal_places=4,
                help_text='Mean annual CO2e sequestered per ha at maturity (IPCC Annex 3A.1)',
            ),
        ),
        migrations.AddField(
            model_name='species',
            name='BiomassDataSource',
            field=models.CharField(
                blank=True, null=True, max_length=200,
                help_text='Citation for biomass parameter values (IPCC table ref, study DOI)',
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restorations', '0002_alter_restorations_options_and_more'),
    ]

    operations = [
        # ── TreeRemovalRemovedSpecies ───────────────────────────────────────────
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='VolumeM3',
            field=models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=4,
                help_text='Merchantable timber volume in m³ (volume-based BEF approach). Per-removal total.'),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='BiomassCalculationMethod',
            field=models.PositiveSmallIntegerField(blank=True, null=True, choices=[
                (1, 'IPCC Tier 1 — default BEF by forest type'),
                (2, 'IPCC Tier 2 — country-specific BEF'),
                (3, 'IPCC Tier 3 — measured / allometric equations'),
                (4, 'Manual entry — pre-calculated values provided directly'),
            ], help_text='Which IPCC tier / approach was used'),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='BiomassCalculationNotes',
            field=models.TextField(blank=True, null=True,
                help_text='Mandatory when BiomassCalculationMethod=4 (Manual) — document source'),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='DeadOrganicMatterTonnesCO2e',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4,
                help_text='Optional Tier 2/3 — CO2e from disturbed dead organic matter'),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='SoilCarbonTonnesCO2e',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4,
                help_text='Optional Tier 3 — CO2e from soil organic carbon disturbance'),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='AboveGroundBiomassTonnes',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='BelowGroundBiomassTonnes',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='TotalBiomassTonnes',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='CarbonStockTonnesC',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='CO2EquivalentTonnes',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        migrations.AddField(
            model_name='treeremovalremovedspecies', name='TotalCarbonStockLossTonnesCO2e',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
        # ── RestorationSpecies ──────────────────────────────────────────────────
        migrations.AddField(
            model_name='restorationspecies', name='AreaHectares',
            field=models.DecimalField(blank=True, null=True, max_digits=12, decimal_places=4,
                help_text='Area planted/restored with this species in hectares'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='AnnualSequestrationRateTonnesCO2ePerHa',
            field=models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=4,
                help_text='Per-record override; defaults to Species.AnnualSequestrationRateTonnesCO2ePerHa'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='SurvivalEstimate',
            field=models.DecimalField(blank=True, null=True, max_digits=4, decimal_places=3, default=0.85,
                help_text='Proportion of planted trees surviving (0–1). Default 0.85 (tropical, unmonitored).'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='LeakageDiscountPercent',
            field=models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2, default=0,
                help_text='% deduction for leakage (0–100). Typically 10–20% for community forestry (VCS VM0047).'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='PermanenceRisk',
            field=models.PositiveSmallIntegerField(blank=True, null=True, choices=[
                (1, 'Low — legally protected, low disturbance risk'),
                (2, 'Medium — some disturbance risk (fire, pest, land tenure)'),
                (3, 'High — significant risk of reversal'),
            ], help_text='Reversal risk (disclosed, not auto-deducted)'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='AdditionalityAssessment',
            field=models.TextField(blank=True, null=True,
                help_text='Narrative additionality assessment. Required for carbon-credit claims.'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='SequestrationDataSource',
            field=models.CharField(blank=True, null=True, max_length=200,
                help_text='Citation for sequestration rate used'),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='YearsEstablished',
            field=models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=2),
        ),
        migrations.AddField(
            model_name='restorationspecies', name='CumulativeSequestrationTonnesCO2e',
            field=models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=4),
        ),
    ]

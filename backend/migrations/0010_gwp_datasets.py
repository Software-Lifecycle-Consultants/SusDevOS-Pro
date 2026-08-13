"""
Migration: GWP Datasets & Values
App: apps.emissions
Depends on: (no FK dependencies — standalone reference tables)

GwpDatasets and GwpValues store the Global Warming Potential factors used in
emissions calculations. A seed data migration (0010_gwp_seed) populates the
IPCC AR6 GWP100 dataset as the default.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        # ── GwpDatasets ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='GwpDatasets',
            fields=[
                ('GwpDatasetId', models.AutoField(primary_key=True)),
                ('Name', models.CharField(
                    max_length=100,
                    help_text="Display name, e.g. 'IPCC AR6 GWP100'"
                )),
                ('Version', models.CharField(
                    max_length=20,
                    help_text="e.g. 'AR6', 'AR5', 'AR4'"
                )),
                ('Horizon', models.PositiveSmallIntegerField(
                    help_text="GWP time horizon in years: 20 or 100"
                )),
                ('IsDefault', models.BooleanField(
                    default=False,
                    help_text="Only one dataset should have IsDefault=True"
                )),
                ('PublishedYear', models.PositiveSmallIntegerField(
                    help_text="Year the dataset was published by the source body"
                )),
                # BaseAuditMixin fields
                ('Status', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1: Active, 2: Disabled, 3: Draft, 4: Deleted"
                )),
                ('ApprovalStatus', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1: Active, 2: Rejected, 3: Pending"
                )),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'gwp_datasets'},
        ),

        # ── GwpValues ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='GwpValues',
            fields=[
                ('GwpValueId', models.AutoField(primary_key=True)),
                ('GwpDatasetId', models.ForeignKey(
                    to='emissions.GwpDatasets',
                    on_delete=models.PROTECT,   # PROTECT: never delete a dataset that has values
                    related_name='gwp_values',
                )),
                ('Gas', models.CharField(
                    max_length=50,
                    help_text="e.g. CO2, CH4, N2O, SF6, HFC-134a"
                )),
                ('GasSubtype', models.CharField(
                    max_length=50,
                    blank=True,
                    null=True,
                    help_text="e.g. 'fossil' or 'biogenic' for CH4"
                )),
                ('GwpFactor', models.DecimalField(
                    max_digits=10,
                    decimal_places=4,
                    help_text="GWP factor relative to CO2 (CO2=1)"
                )),
                # BaseAuditMixin fields
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'gwp_values'},
        ),

        # Unique constraint: one row per gas per dataset
        migrations.AddConstraint(
            model_name='GwpValues',
            constraint=models.UniqueConstraint(
                fields=['GwpDatasetId', 'Gas', 'GasSubtype'],
                name='unique_gwp_gas_per_dataset'
            ),
        ),
    ]


class SeedMigration(migrations.Migration):
    """
    Seed migration: populates IPCC AR6 GWP100 as the default dataset.
    Run after 0010_gwp_datasets.
    """

    dependencies = [
        ('emissions', '0010_gwp_datasets'),
    ]

    def seed_gwp_data(apps, schema_editor):
        GwpDatasets = apps.get_model('emissions', 'GwpDatasets')
        GwpValues = apps.get_model('emissions', 'GwpValues')

        dataset = GwpDatasets.objects.create(
            Name='IPCC AR6 GWP100',
            Version='AR6',
            Horizon=100,
            IsDefault=True,
            PublishedYear=2021,
        )

        # AR6 GWP100 values (Table 7.SM.7, IPCC Sixth Assessment Report)
        gwp_values = [
            ('CO2',  None,        1.0),
            ('CH4',  'fossil',    29.8),
            ('CH4',  'biogenic',  27.9),
            ('N2O',  None,        273.0),
            ('SF6',  None,        25200.0),
            ('NF3',  None,        17400.0),
            # HFCs — most common sub-types
            ('HFC-23',   None, 14800.0),
            ('HFC-32',   None, 771.0),
            ('HFC-125',  None, 3740.0),
            ('HFC-134a', None, 1530.0),
            ('HFC-143a', None, 5810.0),
            ('HFC-152a', None, 164.0),
            ('HFC-227ea',None, 3600.0),
            ('HFC-236fa',None, 8690.0),
            ('HFC-245fa',None, 962.0),
        ]

        GwpValues.objects.bulk_create([
            GwpValues(
                GwpDatasetId=dataset,
                Gas=gas,
                GasSubtype=subtype,
                GwpFactor=factor,
            )
            for gas, subtype, factor in gwp_values
        ])

    operations = [
        migrations.RunPython(seed_gwp_data, migrations.RunPython.noop),
    ]

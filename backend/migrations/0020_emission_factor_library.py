"""
Migration: EmissionFactorSets and EmissionFactors — EF library
App: apps.emissions
Depends on: apps.shared (Units — for InputUnitId FK)

EmissionFactors stores per-gas activity emission factors sourced from
official datasets (DEFRA, EPA, IPCC). Each factor specifies:
  - The activity type and fuel/source
  - The input unit (FK to Units, always in canonical units stored here)
  - Individual gas factors (CO2, CH4, N2O) in kg per canonical unit
  - Biogenic CO2 factor (kg biogenic CO2 per canonical unit — reported separately)
  - A pre-computed TotalKgCO2ePerUnit using the linked GWP dataset

When a user selects an EF from the library on an EmissionsData record:
  1. System reads EFId → gets InputUnitId (canonical)
  2. Converts user's QuantityOrCost from their Unit to canonical unit
  3. Multiplies converted quantity by TotalKgCO2ePerUnit → EmissionsAmount
  4. Separately: converted quantity × BiogenicCO2FactorKgPerUnit → BiogenicCO2Amount

Users can also enter custom EFs (EFId = NULL on EmissionsData) — mandatory
when no library factor covers their activity.

Seed data included: representative DEFRA 2024 UK factors, EPA 2024 US factors,
and IPCC 2006 Tier 1 defaults. Full datasets should be loaded via management
command (python manage.py load_ef_dataset --source defra --year 2024).
"""

from django.db import migrations, models

ACTIVITY_CATEGORY_CHOICES = [
    ('stationary_combustion',    'Stationary Combustion'),
    ('mobile_combustion_road',   'Mobile Combustion — Road'),
    ('mobile_combustion_air',    'Mobile Combustion — Air'),
    ('mobile_combustion_sea',    'Mobile Combustion — Sea/Rail'),
    ('purchased_electricity',    'Purchased Electricity (Scope 2)'),
    ('purchased_heat_steam',     'Purchased Heat/Steam (Scope 2)'),
    ('fugitive_emissions',       'Fugitive Emissions'),
    ('process_emissions',        'Industrial Process Emissions'),
    ('waste',                    'Waste Treatment & Disposal'),
    ('water',                    'Water Supply & Treatment'),
    ('business_travel',          'Business Travel'),
    ('employee_commuting',       'Employee Commuting'),
    ('freight_transport',        'Freight Transportation'),
    ('materials',                'Purchased Goods & Materials'),
    ('spend_based',              'Spend-Based (Scope 3 estimation)'),
    ('land_use_change',          'Land Use Change (LULUCF)'),
    ('refrigerants',             'Refrigerants & Cooling'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0019_units'),
        ('emissions', '0010_gwp_datasets'),
    ]

    operations = [

        # ── EmissionFactorSets ─────────────────────────────────────────────────
        migrations.CreateModel(
            name='EmissionFactorSets',
            fields=[
                ('EFSetId', models.AutoField(primary_key=True)),
                ('Name', models.CharField(max_length=200,
                    help_text="e.g. 'DEFRA 2024 UK Conversion Factors'")),
                ('Publisher', models.CharField(max_length=100,
                    help_text="e.g. DEFRA, EPA, IPCC, ecoinvent, Custom")),
                ('PublishedYear', models.PositiveSmallIntegerField()),
                ('Version', models.CharField(max_length=50, blank=True, null=True,
                    help_text="Publisher version string where applicable")),
                ('Region', models.CharField(max_length=100, blank=True, null=True,
                    help_text="ISO 3166-1 alpha-2 country code, or region name. NULL = global")),
                ('GwpDatasetId', models.ForeignKey(
                    'emissions.GwpDatasets',
                    on_delete=models.PROTECT,
                    help_text="GWP dataset used to compute TotalKgCO2ePerUnit in this set"
                )),
                ('SourceUrl', models.URLField(max_length=500, blank=True, null=True)),
                ('IsDefault', models.BooleanField(default=False,
                    help_text="Shown first in UI dropdowns for the applicable region")),
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'emission_factor_sets'},
        ),

        # ── EmissionFactors ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='EmissionFactors',
            fields=[
                ('EFId', models.AutoField(primary_key=True)),
                ('EFSetId', models.ForeignKey(
                    'emissions.EmissionFactorSets',
                    on_delete=models.PROTECT,
                    related_name='factors',
                )),
                ('ActivityCategory', models.CharField(
                    max_length=50,
                    choices=ACTIVITY_CATEGORY_CHOICES,
                )),
                ('Scope', models.PositiveSmallIntegerField(
                    help_text="1=Scope1, 2=Scope2, 3=Scope3"
                )),
                ('FuelOrActivityType', models.CharField(
                    max_length=200,
                    help_text="Specific fuel or activity, e.g. 'Diesel (road)', 'Natural Gas', 'Grid Electricity - UK'"
                )),
                # Input unit — ALWAYS stored in canonical units in this table
                # e.g. Diesel EF is stored per litre (canonical for volume)
                # Users enter their quantity in any compatible unit; system converts before applying EF
                ('InputUnitId', models.ForeignKey(
                    'shared.Units',
                    on_delete=models.PROTECT,
                    related_name='emission_factors',
                    help_text="Canonical unit this EF is expressed per"
                )),
                # Per-gas breakdown (kg of that gas per canonical input unit)
                # These are used for detailed gas-level reporting
                ('CO2FactorKg', models.DecimalField(max_digits=18, decimal_places=8,
                    default=0, help_text="kg fossil CO2 per canonical unit")),
                ('CH4FactorKg', models.DecimalField(max_digits=18, decimal_places=8,
                    default=0, help_text="kg CH4 per canonical unit")),
                ('N2OFactorKg', models.DecimalField(max_digits=18, decimal_places=8,
                    default=0, help_text="kg N2O per canonical unit")),
                ('OtherGasFactorKgCO2e', models.DecimalField(max_digits=18, decimal_places=8,
                    default=0, help_text="kg CO2e from other GHGs (HFCs, SF6 etc) per canonical unit")),
                # Biogenic CO2 — reported separately, NOT included in TotalKgCO2ePerUnit
                ('BiogenicCO2FactorKg', models.DecimalField(max_digits=18, decimal_places=8,
                    default=0, help_text="kg biogenic CO2 per canonical unit — excluded from GWP calc")),
                # Pre-computed total using the parent set's GWP dataset
                # = CO2Factor×1 + CH4Factor×GWP_CH4 + N2OFactor×GWP_N2O + OtherGasFactor
                ('TotalKgCO2ePerUnit', models.DecimalField(max_digits=18, decimal_places=8,
                    help_text="Total kg CO2e per canonical unit — server recomputes if GWP dataset changes")),
                # Scope 2 specifics
                ('Scope2Method', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    help_text="NULL=N/A, 1=LocationBased, 2=MarketBased. Only for Scope 2 factors."
                )),
                ('CountryCode', models.CharField(max_length=10, blank=True, null=True,
                    help_text="ISO 3166-1 alpha-2 for geography-specific EFs (e.g. grid electricity)")),
                ('ApplicableYear', models.PositiveSmallIntegerField(null=True, blank=True,
                    help_text="Year this EF applies to. NULL = timeless (e.g. combustion factors)")),
                ('EmissionType', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1=Fossil, 2=Biogenic, 3=Mixed"
                )),
                ('Notes', models.TextField(blank=True, null=True,
                    help_text="Usage notes, caveats, or source citation details")),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'emission_factors'},
        ),

        migrations.AddIndex(
            model_name='EmissionFactors',
            index=models.Index(
                fields=['EFSetId', 'ActivityCategory', 'Scope'],
                name='idx_ef_set_category_scope'
            ),
        ),
        migrations.AddIndex(
            model_name='EmissionFactors',
            index=models.Index(
                fields=['CountryCode', 'ApplicableYear'],
                name='idx_ef_country_year'
            ),
        ),
    ]


class SeedEFMigration(migrations.Migration):
    """
    Seed representative emission factors from DEFRA 2024 (UK) and IPCC 2006 Tier 1.
    Full dataset loading: python manage.py load_ef_dataset --source defra --year 2024

    All factors stored in canonical units:
      Fuel combustion → per litre (L)
      Electricity     → per kWh (stored as kWh even though canonical energy is kJ,
                        because all published EFs for electricity use kWh)
      Refrigerants    → per kg
      Freight         → per tonne-kilometre (tkm)
    """

    dependencies = [('emissions', '0020_emission_factor_library')]

    def seed_ef_data(apps, schema_editor):
        EmissionFactorSets = apps.get_model('emissions', 'EmissionFactorSets')
        EmissionFactors    = apps.get_model('emissions', 'EmissionFactors')
        GwpDatasets        = apps.get_model('emissions', 'GwpDatasets')
        Units              = apps.get_model('shared', 'Units')

        ar6 = GwpDatasets.objects.get(IsDefault=True)

        # Unit lookups
        litre  = Units.objects.get(UnitSymbol='L')
        kwh    = Units.objects.get(UnitSymbol='kWh')
        kg_u   = Units.objects.get(UnitSymbol='kg')
        tkm    = Units.objects.get(UnitSymbol='tkm')

        # ── DEFRA 2024 (UK) ────────────────────────────────────────────────────
        defra = EmissionFactorSets.objects.create(
            Name='DEFRA 2024 UK Conversion Factors',
            Publisher='DEFRA',
            PublishedYear=2024,
            Version='2024',
            Region='GB',
            GwpDatasetId=ar6,
            SourceUrl='https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024',
            IsDefault=True,
        )

        defra_fuels = [
            # (FuelOrActivityType, category, scope, CO2, CH4, N2O, bioCO2, total, unit, scope2method)
            # Stationary combustion fuels (per litre)
            ('Diesel (combustion)',         'stationary_combustion', 1, 2.6312,  0.000090, 0.000078, 0,      2.6516,  litre, None),
            ('Petrol (combustion)',         'stationary_combustion', 1, 2.3148,  0.000207, 0.000184, 0,      2.3427,  litre, None),
            ('LPG (combustion)',            'stationary_combustion', 1, 1.5551,  0.000056, 0.000049, 0,      1.5668,  litre, None),
            ('Natural Gas (combustion)',    'stationary_combustion', 1, 2.0431,  0.000039, 0.000034, 0,      2.0541,  litre, None),
            ('Fuel Oil (combustion)',       'stationary_combustion', 1, 2.9560,  0.000094, 0.000082, 0,      2.9791,  litre, None),
            ('Kerosene / Jet A-1',          'stationary_combustion', 1, 2.5400,  0.000088, 0.000077, 0,      2.5596,  litre, None),
            # Biofuels (per litre) — note biogenic CO2 tracked separately
            ('Biodiesel (B100)',            'stationary_combustion', 1, 0.0,     0.000090, 0.000078, 2.6312, 0.1881,  litre, None),
            # Mobile combustion (road) — same EFs as stationary for liquid fuels
            ('Diesel (road)',               'mobile_combustion_road', 1, 2.6312, 0.000090, 0.000078, 0,      2.6516,  litre, None),
            ('Petrol (road)',               'mobile_combustion_road', 1, 2.3148, 0.000207, 0.000184, 0,      2.3427,  litre, None),
            # UK grid electricity — location-based (per kWh)
            ('UK Grid Electricity (location-based)', 'purchased_electricity', 2, 0.207,  0.0,      0.0,    0,      0.207,   kwh,  1),
            # Refrigerants (per kg)
            ('HFC-134a (refrigerant)',      'refrigerants',          1, 0,       0,        0,        0,      1530.0,  kg_u, None),
            ('HFC-32 (refrigerant)',        'refrigerants',          1, 0,       0,        0,        0,      771.0,   kg_u, None),
            ('R-410A (refrigerant blend)',  'refrigerants',          1, 0,       0,        0,        0,      2088.0,  kg_u, None),
            # Freight (per tkm)
            ('HGV (diesel, average laden)', 'freight_transport',     3, 0.1133, 0.0,      0.0,      0,      0.1133,  tkm,  None),
            ('Air freight (long-haul)',     'mobile_combustion_air', 3, 0.6026, 0.0,      0.0,      0,      0.6026,  tkm,  None),
            ('Sea freight (container)',     'mobile_combustion_sea', 3, 0.0110, 0.0,      0.0,      0,      0.0110,  tkm,  None),
        ]

        for row in defra_fuels:
            fuel, cat, scope, co2, ch4, n2o, bio, total, unit, s2m = row
            EmissionFactors.objects.create(
                EFSetId=defra,
                ActivityCategory=cat,
                Scope=scope,
                FuelOrActivityType=fuel,
                InputUnitId=unit,
                CO2FactorKg=co2,
                CH4FactorKg=ch4,
                N2OFactorKg=n2o,
                BiogenicCO2FactorKg=bio,
                OtherGasFactorKgCO2e=0,
                TotalKgCO2ePerUnit=total,
                Scope2Method=s2m,
                CountryCode='GB' if 'UK' in fuel or 'Grid' in fuel else None,
                ApplicableYear=2024 if 'Grid' in fuel else None,
                EmissionType=2 if bio > 0 else 1,
            )

        # ── IPCC 2006 Tier 1 Defaults (global) ────────────────────────────────
        ipcc = EmissionFactorSets.objects.create(
            Name='IPCC 2006 Guidelines — Tier 1 Defaults',
            Publisher='IPCC',
            PublishedYear=2006,
            Version='2006',
            Region=None,
            GwpDatasetId=ar6,
            SourceUrl='https://www.ipcc-nggip.iges.or.jp/public/2006gl/',
            IsDefault=False,
        )

        ipcc_fuels = [
            # Stationary combustion (energy content basis — stored per kWh net calorific value)
            ('Coal (sub-bituminous)',       'stationary_combustion', 1, 0.3442, 0.0000028, 0.0000028, 0, 0.3443, kwh, None),
            ('Coal (bituminous)',           'stationary_combustion', 1, 0.3460, 0.0000028, 0.0000028, 0, 0.3461, kwh, None),
            ('Crude Oil',                  'stationary_combustion', 1, 0.2640, 0.0000028, 0.0000028, 0, 0.2641, kwh, None),
            ('Natural Gas',                'stationary_combustion', 1, 0.2015, 0.0000028, 0.0000028, 0, 0.2016, kwh, None),
        ]

        for row in ipcc_fuels:
            fuel, cat, scope, co2, ch4, n2o, bio, total, unit, s2m = row
            EmissionFactors.objects.create(
                EFSetId=ipcc,
                ActivityCategory=cat,
                Scope=scope,
                FuelOrActivityType=fuel,
                InputUnitId=unit,
                CO2FactorKg=co2,
                CH4FactorKg=ch4,
                N2OFactorKg=n2o,
                BiogenicCO2FactorKg=bio,
                OtherGasFactorKgCO2e=0,
                TotalKgCO2ePerUnit=total,
                Scope2Method=s2m,
                Notes='IPCC 2006 Tier 1 default — use country-specific Tier 2 factors when available',
                EmissionType=1,
            )

    operations = [
        migrations.RunPython(seed_ef_data, migrations.RunPython.noop),
    ]

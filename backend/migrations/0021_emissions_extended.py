"""
Migration: Extend EmissionsData
App: apps.emissions
Depends on: 0011_emissions, 0019_units, 0020_emission_factor_library

Adds to EmissionsData:
  1. InputUnitId FK → Units  (replaces free-text Unit CharField)
  2. EFId FK → EmissionFactors  (optional library reference; NULL = custom EF)
  3. Scope 2 dual-method fields  (LocationBased + MarketBased amounts)
  4. Biogenic CO2 amount  (reported separately, excluded from total CO2e)
  5. InventoryId FK → GHGInventories  (links record to a formal inventory period)
  6. Extended verification fields  (standard, assurance level, verifier org)

IMPORTANT: The free-text Unit field on EmissionsData is NOT dropped in this
migration to allow data migration. A follow-up data migration should populate
InputUnitId from Unit text, then a final migration drops the Unit column.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0011_emissions'),
        ('shared', '0019_units'),
        ('emissions', '0020_emission_factor_library'),
        # GHGInventories is in 0022 — use AddField after that migration
        # to avoid circular dependency; InventoryId added in 0022 instead.
    ]

    operations = [

        # 1. InputUnitId — FK to Units (canonical unit for this activity)
        migrations.AddField(
            model_name='EmissionsData',
            name='InputUnitId',
            field=models.ForeignKey(
                'shared.Units',
                on_delete=models.PROTECT,
                null=True,
                blank=True,
                related_name='emissions_using_unit',
                help_text=(
                    "Unit the user entered QuantityOrCost in. "
                    "System converts to canonical unit before applying EF. "
                    "Populate this; the legacy Unit CharField will be removed in a future migration."
                )
            ),
        ),

        # 2. EFId — optional FK to library emission factor
        migrations.AddField(
            model_name='EmissionsData',
            name='EFId',
            field=models.ForeignKey(
                'emissions.EmissionFactors',
                on_delete=models.PROTECT,
                null=True,
                blank=True,
                related_name='emissions_using_factor',
                help_text=(
                    "Library emission factor used. NULL = user entered custom EmissionFactor. "
                    "When set, EmissionFactor and EmissionFactorSource are auto-populated from library."
                )
            ),
        ),

        # 3a. Scope 2 method discriminator
        migrations.AddField(
            model_name='EmissionsData',
            name='Scope2Method',
            field=models.PositiveSmallIntegerField(
                null=True,
                blank=True,
                help_text="NULL for Scope 1 & 3. 1=LocationBased, 2=MarketBased. GHG Protocol requires BOTH for Scope 2."
            ),
        ),

        # 3b. Location-based Scope 2 fields
        migrations.AddField(
            model_name='EmissionsData',
            name='EFLocationBased',
            field=models.DecimalField(
                max_digits=18, decimal_places=8,
                null=True, blank=True,
                help_text="Location-based EF (kg CO2e per canonical unit) — grid average EF for country/region"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EFLocationBasedSource',
            field=models.CharField(max_length=200, null=True, blank=True,
                help_text="Source for location-based EF (e.g. IEA 2023, DEFRA 2024 Grid)"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EmissionsAmountLocationBased',
            field=models.DecimalField(max_digits=18, decimal_places=4,
                null=True, blank=True,
                help_text="Calculated: QuantityCanonical × EFLocationBased (kg CO2e)"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EmissionsAmountLocationBasedTonnes',
            field=models.DecimalField(max_digits=18, decimal_places=6,
                null=True, blank=True,
                help_text="EmissionsAmountLocationBased / 1000 (tCO2e)"
            ),
        ),

        # 3c. Market-based Scope 2 fields
        migrations.AddField(
            model_name='EmissionsData',
            name='EFMarketBased',
            field=models.DecimalField(
                max_digits=18, decimal_places=8,
                null=True, blank=True,
                help_text="Market-based EF — supplier-specific or residual mix EF"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EFMarketBasedSource',
            field=models.CharField(max_length=200, null=True, blank=True,
                help_text="Source: e.g. 'Supplier EF certificate', 'RE100 residual mix 2024', 'PPA contract'"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EmissionsAmountMarketBased',
            field=models.DecimalField(max_digits=18, decimal_places=4,
                null=True, blank=True,
                help_text="Calculated: QuantityCanonical × EFMarketBased (kg CO2e)"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='EmissionsAmountMarketBasedTonnes',
            field=models.DecimalField(max_digits=18, decimal_places=6,
                null=True, blank=True,
                help_text="EmissionsAmountMarketBased / 1000 (tCO2e)"
            ),
        ),

        # 4. Biogenic CO2 (reported separately — excluded from GWP-weighted total)
        migrations.AddField(
            model_name='EmissionsData',
            name='BiogenicCO2Amount',
            field=models.DecimalField(max_digits=18, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "Biogenic CO2 in kg — reported separately per GHG Protocol. "
                    "NOT included in EmissionsAmount or EmissionsAmountTonnes. "
                    "Calculated from EF.BiogenicCO2FactorKg or entered manually."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='BiogenicCO2AmountTonnes',
            field=models.DecimalField(max_digits=18, decimal_places=6,
                null=True, blank=True,
                help_text="BiogenicCO2Amount / 1000"
            ),
        ),

        # 5. Canonical quantity (stored for auditability after unit conversion)
        migrations.AddField(
            model_name='EmissionsData',
            name='QuantityCanonical',
            field=models.DecimalField(max_digits=18, decimal_places=8,
                null=True, blank=True,
                help_text="QuantityOrCost converted to canonical unit. Server-populated on save."
            ),
        ),

        # 6. Extended verification fields
        migrations.AddField(
            model_name='EmissionsData',
            name='VerificationStandard',
            field=models.CharField(max_length=100, null=True, blank=True,
                help_text="e.g. 'ISO 14064-3', 'ISAE 3410', 'GHG Protocol'"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='AssuranceLevel',
            field=models.PositiveSmallIntegerField(null=True, blank=True,
                help_text="1=Limited Assurance, 2=Reasonable Assurance"
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='VerifierOrganisation',
            field=models.CharField(max_length=200, null=True, blank=True,
                help_text="Name of the third-party verification body"
            ),
        ),

        # 7. Data quality indicator (per ISO 14064-1 and GHG Protocol)
        migrations.AddField(
            model_name='EmissionsData',
            name='DataQuality',
            field=models.PositiveSmallIntegerField(null=True, blank=True,
                help_text=(
                    "1=Measured (primary data from meters/invoices), "
                    "2=Calculated (activity data × published EF), "
                    "3=Estimated (engineering estimates), "
                    "4=Modelled (simulation/LCA)"
                )
            ),
        ),
    ]

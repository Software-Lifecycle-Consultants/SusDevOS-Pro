"""
Migration: API Integration Fields
App: apps.emissions, apps.entities, apps.shared, apps.ecosystem
Depends on: 0025_scope3_relevance, 0026_entity_consolidation, ecosystem.0001, restorations.0001

Adds fields and tables required by the external API integrations defined in
spec/api_integrations.md. All new fields are nullable with blank=True so
existing records are unaffected — integration fields are populated progressively
as users interact with the lookup features.

New table:
  ExchangeRates — daily FX rates from ECB / Open Exchange Rates

Fields added to existing models:
  Entities          — CompaniesHouseNumber, SBTiCompanyId, SICCodes, IncorporationDate
  EmissionFactors   — ClimatiqActivityId, GridSubregion, ExternalSyncedAt
  EmissionsData     — SpendCurrency, SpendAmountLocal, ExchangeRateToUSD,
                      ExchangeRateDate, SpendAmountUSD, GridSubregion
  EmissionsOffsets  — CreditSerialNumber, RegistryValidatedAt,
                      RegistryValidationStatus, RegistryProjectName,
                      RegistryProjectType, RegistryVintageYear,
                      RegistryRetirementBeneficiary
  Targets           — SBTiCompanyId (mirror from entity), SBTiStatus, SBTiLastSyncedAt
  Species           — GBIFKey, ScientificName, IUCNStatus, IUCNSyncedAt
"""

from django.db import migrations, models
import django.db.models.deletion


REGISTRY_VALIDATION_STATUS = [
    ('pending',    'Pending — not yet validated'),
    ('valid',      'Valid — confirmed in registry'),
    ('invalid',    'Invalid — not found or retired by another party'),
    ('unverified', 'Unverified — validation skipped'),
]

IUCN_STATUS_CHOICES = [
    ('LC', 'Least Concern'),
    ('NT', 'Near Threatened'),
    ('VU', 'Vulnerable'),
    ('EN', 'Endangered'),
    ('CR', 'Critically Endangered'),
    ('EW', 'Extinct in the Wild'),
    ('EX', 'Extinct'),
    ('DD', 'Data Deficient'),
    ('NE', 'Not Evaluated'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0025_scope3_relevance'),
        ('entities', '0026_entity_consolidation'),
        ('ecosystem', '0001_ecosystem_species'),
    ]

    operations = [

        # ── ExchangeRates — daily FX cache ────────────────────────────────────
        migrations.CreateModel(
            name='ExchangeRates',
            fields=[
                ('RateId', models.AutoField(primary_key=True)),
                ('FromCurrency', models.CharField(
                    max_length=3,
                    help_text="ISO 4217 source currency code (e.g. GBP, EUR, AUD)"
                )),
                ('ToCurrency', models.CharField(
                    max_length=3,
                    default='USD',
                    help_text="ISO 4217 target currency (always USD for spend-based EF calculations)"
                )),
                ('Rate', models.DecimalField(
                    max_digits=18, decimal_places=8,
                    help_text="Units of ToCurrency per 1 unit of FromCurrency"
                )),
                ('RateDate', models.DateField(
                    help_text="Date this rate was published (ECB publishes ~16:00 CET daily)"
                )),
                ('Source', models.CharField(
                    max_length=50,
                    help_text="'ECB' | 'OpenExchangeRates'"
                )),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
            ],
            options={'db_table': 'exchange_rates'},
        ),
        migrations.AddConstraint(
            model_name='ExchangeRates',
            constraint=models.UniqueConstraint(
                fields=['FromCurrency', 'ToCurrency', 'RateDate'],
                name='unique_fx_rate_per_currency_pair_date'
            ),
        ),
        migrations.AddIndex(
            model_name='ExchangeRates',
            index=models.Index(
                fields=['FromCurrency', 'ToCurrency', 'RateDate'],
                name='idx_fx_currency_date'
            ),
        ),

        # ── Entities: external registry IDs ───────────────────────────────────
        migrations.AddField(
            model_name='Entities',
            name='CompaniesHouseNumber',
            field=models.CharField(
                max_length=20, null=True, blank=True,
                help_text=(
                    "UK Companies House registration number (8 characters). "
                    "Used to auto-populate entity details and sync from Companies House API."
                )
            ),
        ),
        migrations.AddField(
            model_name='Entities',
            name='SBTiCompanyId',
            field=models.CharField(
                max_length=50, null=True, blank=True,
                help_text=(
                    "SBTi company identifier from the SBTi Companies Taking Action registry. "
                    "Used for exact matching during monthly SBTi sync task. "
                    "If NULL, fuzzy name matching is used (requires manual review)."
                )
            ),
        ),
        migrations.AddField(
            model_name='Entities',
            name='SICCodes',
            field=models.JSONField(
                default=list, blank=True,
                help_text=(
                    "List of UK SIC codes from Companies House (e.g. ['35110', '35120']). "
                    "Used to suggest the relevant SBTi sector decarbonization pathway."
                )
            ),
        ),
        migrations.AddField(
            model_name='Entities',
            name='IncorporationDate',
            field=models.DateField(
                null=True, blank=True,
                help_text="Date of incorporation from Companies House."
            ),
        ),
        migrations.AddField(
            model_name='Entities',
            name='ExternalRegistryUrl',
            field=models.URLField(
                null=True, blank=True,
                help_text=(
                    "Direct link to this entity's entry in an external registry "
                    "(Companies House, OpenCorporates, etc.). Auto-populated."
                )
            ),
        ),

        # ── EmissionFactors: Climatiq external key + grid subregion ───────────
        migrations.AddField(
            model_name='EmissionFactors',
            name='ClimatiqActivityId',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text=(
                    "Climatiq activity_id string used to fetch and refresh this factor. "
                    "e.g. 'electricity-supply_grid-source_residual_mix'. "
                    "NULL for manually entered or DEFRA/EPA bulk-imported factors."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionFactors',
            name='GridSubregion',
            field=models.CharField(
                max_length=50, null=True, blank=True,
                help_text=(
                    "US eGRID subregion code (e.g. 'WECC_CA', 'ERCOT', 'NPCC_NYC'). "
                    "Only populated for US electricity EFs. "
                    "Used to match EmissionsData.GridSubregion for location-based Scope 2."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionFactors',
            name='ExternalSyncedAt',
            field=models.DateTimeField(
                null=True, blank=True,
                help_text=(
                    "Timestamp of last sync from external source (Climatiq, DEFRA, EPA). "
                    "NULL = manually entered. Used to detect stale factors (>365 days)."
                )
            ),
        ),

        # ── EmissionsData: spend-based FX fields + grid subregion ─────────────
        migrations.AddField(
            model_name='EmissionsData',
            name='SpendCurrency',
            field=models.CharField(
                max_length=3, null=True, blank=True,
                help_text=(
                    "ISO 4217 currency code for spend-based Scope 3 activity data. "
                    "e.g. 'GBP', 'EUR'. NULL for non-spend-based records. "
                    "Required when QuantityOrCost is a monetary amount."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='SpendAmountLocal',
            field=models.DecimalField(
                max_digits=18, decimal_places=2, null=True, blank=True,
                help_text="Original spend in SpendCurrency before FX conversion."
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='SpendAmountUSD',
            field=models.DecimalField(
                max_digits=18, decimal_places=2, null=True, blank=True,
                help_text=(
                    "SpendAmountLocal converted to USD. "
                    "Used as QuantityCanonical for spend-based emission factor application."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='ExchangeRateToUSD',
            field=models.DecimalField(
                max_digits=18, decimal_places=8, null=True, blank=True,
                help_text=(
                    "FX rate applied: units of USD per 1 unit of SpendCurrency. "
                    "Snapshot stored for audit trail — rate at time of data entry."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='ExchangeRateDate',
            field=models.DateField(
                null=True, blank=True,
                help_text="Date of the ExchangeRateToUSD snapshot (from ECB daily rate)."
            ),
        ),
        migrations.AddField(
            model_name='EmissionsData',
            name='GridSubregion',
            field=models.CharField(
                max_length=50, null=True, blank=True,
                help_text=(
                    "US eGRID subregion for this record (e.g. 'ERCOT'). "
                    "Required for US electricity Scope 2 location-based calculation. "
                    "Auto-populated from entity address if US state is known."
                )
            ),
        ),

        # ── EmissionsOffsets: registry validation fields ───────────────────────
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='CreditSerialNumber',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text=(
                    "Registry serial number or block range for this credit. "
                    "e.g. Verra format: 'VCS-1234-2020-01-01-...' "
                    "Used to validate against Verra/Gold Standard registry."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryValidatedAt',
            field=models.DateTimeField(
                null=True, blank=True,
                help_text="Timestamp of last registry validation check."
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryValidationStatus',
            field=models.CharField(
                max_length=20, null=True, blank=True,
                choices=REGISTRY_VALIDATION_STATUS,
                default='unverified',
                help_text=(
                    "Result of last registry validation. "
                    "Credits are only applied to NetEmissions when status='valid'."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryProjectName',
            field=models.CharField(
                max_length=300, null=True, blank=True,
                help_text="Project name from registry (auto-populated on validation)."
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryProjectType',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text=(
                    "Project methodology/type from registry. "
                    "e.g. 'Avoided Deforestation (REDD+)', 'Cookstoves', 'Solar'. "
                    "Disclosed in GHG inventory per GHG Protocol offset reporting requirements."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryVintageYear',
            field=models.PositiveSmallIntegerField(
                null=True, blank=True,
                help_text=(
                    "Year the emission reduction/removal represented by this credit occurred. "
                    "From registry — must match user-entered vintage for validation to pass."
                )
            ),
        ),
        migrations.AddField(
            model_name='EmissionsOffsets',
            name='RegistryRetirementBeneficiary',
            field=models.CharField(
                max_length=300, null=True, blank=True,
                help_text=(
                    "Name of the retirement beneficiary from registry. "
                    "Should match the entity name to confirm the credit belongs to this inventory."
                )
            ),
        ),

        # ── Targets: SBTi registry sync fields ────────────────────────────────
        migrations.AddField(
            model_name='Targets',
            name='SBTiStatus',
            field=models.CharField(
                max_length=50, null=True, blank=True,
                help_text=(
                    "SBTi status string from the Companies Taking Action registry. "
                    "e.g. 'Targets Set', 'Committed', 'Achieved'. "
                    "Auto-populated by monthly SBTi sync task. "
                    "Maps to ValidationStatus on upsert."
                )
            ),
        ),
        migrations.AddField(
            model_name='Targets',
            name='SBTiLastSyncedAt',
            field=models.DateTimeField(
                null=True, blank=True,
                help_text="Timestamp of last successful SBTi registry sync for this target."
            ),
        ),

        # ── Species: GBIF + IUCN fields ───────────────────────────────────────
        migrations.AddField(
            model_name='Species',
            name='GBIFKey',
            field=models.PositiveIntegerField(
                null=True, blank=True,
                help_text=(
                    "GBIF species key (integer). Unique identifier in the Global Biodiversity "
                    "Information Facility database. Used to refresh taxonomy data."
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='ScientificName',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text=(
                    "Accepted scientific name (binomial) from GBIF. "
                    "e.g. 'Shorea robusta'. Required for IPCC biomass parameter lookup "
                    "and IUCN Red List status retrieval."
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='Family',
            field=models.CharField(
                max_length=100, null=True, blank=True,
                help_text="Taxonomic family from GBIF (e.g. 'Dipterocarpaceae')."
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='Kingdom',
            field=models.CharField(
                max_length=50, null=True, blank=True,
                help_text="Taxonomic kingdom from GBIF (e.g. 'Plantae')."
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='IUCNStatus',
            field=models.CharField(
                max_length=2, null=True, blank=True,
                choices=IUCN_STATUS_CHOICES,
                help_text=(
                    "IUCN Red List conservation status. "
                    "Disclosed in biodiversity impact reports and TNFD disclosures."
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='IUCNSyncedAt',
            field=models.DateTimeField(
                null=True, blank=True,
                help_text="Timestamp of last IUCN Red List API call for this species."
            ),
        ),

        # ── Indexes ───────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='EmissionFactors',
            index=models.Index(
                fields=['ClimatiqActivityId', 'CountryCode', 'ApplicableYear'],
                name='idx_ef_climatiq_key'
            ),
        ),
        migrations.AddIndex(
            model_name='Species',
            index=models.Index(
                fields=['GBIFKey'],
                name='idx_species_gbif_key'
            ),
        ),
        migrations.AddIndex(
            model_name='EmissionsOffsets',
            index=models.Index(
                fields=['CreditSerialNumber'],
                name='idx_offset_serial_number'
            ),
        ),
    ]

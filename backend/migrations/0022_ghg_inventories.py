"""
Migration: GHGInventories + link EmissionsData to inventory
App: apps.emissions
Depends on: 0021_emissions_extended, apps.entities, apps.users

A GHGInventory is a formal, bounded collection of emissions records for a
specific entity and reporting period. This is the correct level at which
third-party verification is applied — not to individual EmissionsData records.

Key rules:
- One entity can have at most one inventory per reporting year (enforced via
  UniqueConstraint on EntityId + ReportingYear).
- EmissionsData.InventoryId links individual records to an inventory.
- Totals (Scope1/2/3) are computed on-demand by the reporting engine and
  can be cached here for performance. Set to NULL to trigger recomputation.
- VerificationStatus on GHGInventory is the authoritative verification flag.
  The VerificationStatus on EmissionsData records individual data quality,
  NOT whether the record has been third-party verified.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emissions', '0021_emissions_extended'),
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
    ]

    operations = [

        # ── GHGInventories ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='GHGInventories',
            fields=[
                ('InventoryId', models.AutoField(primary_key=True)),
                ('EntityId', models.ForeignKey(
                    'entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='ghg_inventories',
                )),
                ('ReportingYear', models.PositiveSmallIntegerField(
                    help_text="4-digit calendar year of the reporting period"
                )),
                ('ReportingPeriodFrom', models.DateField()),
                ('ReportingPeriodTo', models.DateField()),
                # Consolidation approach for this inventory
                # (may differ from entity default if approach changed mid-year)
                ('ConsolidationApproach', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    help_text="1=EquityShare, 2=FinancialControl, 3=OperationalControl"
                )),
                ('BaselineYear', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    help_text="Base year for intensity/reduction comparisons"
                )),
                # Inventory-level verification (third-party assurance)
                ('VerificationStatus', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1=Unverified, 2=PendingVerification, 3=VerifiedLimited, 4=VerifiedReasonable"
                )),
                ('VerificationStandard', models.CharField(max_length=100, null=True, blank=True,
                    help_text="e.g. 'ISO 14064-3', 'ISAE 3410'"
                )),
                ('AssuranceLevel', models.PositiveSmallIntegerField(null=True, blank=True,
                    help_text="1=Limited, 2=Reasonable"
                )),
                ('VerifierOrganisation', models.CharField(max_length=200, null=True, blank=True)),
                ('VerifiedBy', models.ForeignKey(
                    'users.Users',
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='verified_inventories',
                    help_text="Internal user who submitted for verification"
                )),
                ('VerifiedAt', models.DateTimeField(null=True, blank=True)),
                # Cached totals — set to NULL to force recomputation
                ('TotalScope1Tonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text="Scope 1 total tCO2e — cached from EmissionsData aggregation"
                )),
                ('TotalScope2LocationBasedTonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True
                )),
                ('TotalScope2MarketBasedTonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True
                )),
                ('TotalScope3Tonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True
                )),
                ('TotalBiogenicCO2Tonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text="Total biogenic CO2 tCO2 — reported separately, not in GWP total"
                )),
                ('TotalOffsetsAppliedTonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True
                )),
                # Net emissions = Scope1 + Scope2(market) + Scope3 − Offsets
                ('NetEmissionsTonnes', models.DecimalField(max_digits=18, decimal_places=4,
                    null=True, blank=True
                )),
                ('TotalsLastComputedAt', models.DateTimeField(null=True, blank=True,
                    help_text="Timestamp of last aggregation. NULL = needs recomputation."
                )),
                ('Notes', models.TextField(null=True, blank=True)),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'ghg_inventories'},
        ),

        # One inventory per entity per year
        migrations.AddConstraint(
            model_name='GHGInventories',
            constraint=models.UniqueConstraint(
                fields=['EntityId', 'ReportingYear'],
                name='unique_inventory_per_entity_year'
            ),
        ),

        # Link EmissionsData → GHGInventories
        migrations.AddField(
            model_name='EmissionsData',
            name='InventoryId',
            field=models.ForeignKey(
                'emissions.GHGInventories',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='emissions_records',
                help_text="Formal GHG inventory this record belongs to. NULL = unassigned draft."
            ),
        ),

        migrations.AddIndex(
            model_name='GHGInventories',
            index=models.Index(
                fields=['EntityId', 'ReportingYear'],
                name='idx_inventory_entity_year'
            ),
        ),
    ]

"""
Migration: EmissionsData, EmissionsDetails, EmissionsOffsets
App: apps.emissions
Depends on: apps.entities, apps.projects, apps.emissions (gwp_datasets)

This is the core domain model for GHG tracking.

Calculation rule (enforced in EmissionsData.save()):
  EmissionsAmount (kg CO2e) = QuantityOrCost × EmissionFactor × GWP_factor
  EmissionsAmountTonnes = EmissionsAmount / 1000

Auto-calculation is server-side only. Frontend sends raw quantities.
Never trust client-computed totals.

Verified records (VerificationStatus=3) are immutable — blocked at the
serializer layer. Only SuperAdmin can unlock via POST /emissions/{id}/unlock/.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('projects', '0001_development_projects'),
        ('emissions', '0010_gwp_datasets'),
    ]

    operations = [

        # ── EmissionsData ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='EmissionsData',
            fields=[
                ('EmissionsId', models.AutoField(primary_key=True)),
                # Tenant isolation — required on every queryable table
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='emissions_records',
                    help_text="Owning entity — enforced by TenantQueryMiddleware"
                )),
                ('ProjectId', models.ForeignKey(
                    to='projects.DevelopmentProjects',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='emissions_records',
                )),
                ('PhaseId', models.ForeignKey(
                    to='projects.ProjectPhases',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='emissions_records',
                )),
                ('Title', models.CharField(max_length=200)),
                # GHG Protocol Scope
                ('Scope', models.PositiveSmallIntegerField(
                    help_text="1: Scope 1 (direct), 2: Scope 2 (electricity), 3: Scope 3 (value chain)"
                )),
                ('Scope3Category', models.PositiveSmallIntegerField(
                    null=True,
                    blank=True,
                    help_text="1–15: GHG Protocol Scope 3 sub-categories. NULL for Scope 1 and 2."
                )),
                ('ActivityDescription', models.TextField(
                    blank=True,
                    null=True,
                    help_text="Description of the emission-generating activity"
                )),
                # Raw inputs (sent by frontend)
                ('QuantityOrCost', models.DecimalField(
                    max_digits=18,
                    decimal_places=4,
                    help_text="Activity quantity in the specified unit (e.g. litres, kWh, km)"
                )),
                ('Unit', models.CharField(
                    max_length=50,
                    help_text="Unit of QuantityOrCost (e.g. litres, kWh, km, tonne)"
                )),
                ('EmissionFactor', models.DecimalField(
                    max_digits=18,
                    decimal_places=8,
                    help_text="kg of gas per unit of activity from the emission factor source"
                )),
                ('EmissionFactorSource', models.CharField(
                    max_length=200,
                    help_text="Source of emission factor (e.g. IPCC, DEFRA, EPA, custom)"
                )),
                ('Gas', models.CharField(
                    max_length=50,
                    help_text="Greenhouse gas (e.g. CO2, CH4, N2O, SF6, HFC-134a)"
                )),
                ('GasSubtype', models.CharField(
                    max_length=50,
                    null=True,
                    blank=True,
                    help_text="e.g. 'fossil' or 'biogenic' for CH4"
                )),
                # GWP reference
                ('GwpDatasetId', models.ForeignKey(
                    to='emissions.GwpDatasets',
                    on_delete=models.PROTECT,
                    related_name='emissions_records',
                    help_text="GWP dataset used for this calculation — never changes after save"
                )),
                # Calculated fields (server-side only, never accept from client)
                ('EmissionsAmount', models.DecimalField(
                    max_digits=18,
                    decimal_places=4,
                    null=True,
                    blank=True,
                    help_text="Calculated: QuantityOrCost × EmissionFactor × GWP_factor (kg CO2e)"
                )),
                ('EmissionsAmountTonnes', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    null=True,
                    blank=True,
                    help_text="Calculated: EmissionsAmount / 1000 (tCO2e)"
                )),
                ('EmissionsReduced', models.DecimalField(
                    max_digits=18,
                    decimal_places=4,
                    null=True,
                    blank=True,
                    help_text="Reduction amount in kg CO2e (e.g. from efficiency measures)"
                )),
                ('EmissionsReducedTonnes', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    null=True,
                    blank=True,
                    help_text="EmissionsReduced / 1000 (tCO2e)"
                )),
                # Reporting period
                ('BaselineYear', models.PositiveSmallIntegerField(
                    null=True,
                    blank=True,
                    help_text="Baseline year for GHG reporting (4-digit year)"
                )),
                ('ReportingPeriodFrom', models.DateField(
                    null=True,
                    blank=True,
                )),
                ('ReportingPeriodTo', models.DateField(
                    null=True,
                    blank=True,
                )),
                # Verification
                ('VerificationStatus', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1: Unverified, 2: Pending Verification, 3: Verified (immutable)"
                )),
                ('VerifiedBy', models.ForeignKey(
                    to='users.Users',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='verified_emissions',
                )),
                ('VerifiedAt', models.DateTimeField(null=True, blank=True)),
                ('VerificationNotes', models.TextField(null=True, blank=True)),
                ('CountsTowardNDC', models.BooleanField(
                    default=False,
                    help_text="Include this record in national/governmental reporting aggregations"
                )),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(
                    default=1,
                    help_text="1: Active, 2: Disabled, 3: Draft, 4: Deleted"
                )),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'emissions_data'},
        ),

        # ── EmissionsDetails ───────────────────────────────────────────────────
        # Line-item breakdown within an EmissionsData record.
        # Used for Scope 3 multi-activity records or when a single record
        # needs sub-items (e.g. breakdown by fuel type or vehicle).
        migrations.CreateModel(
            name='EmissionsDetails',
            fields=[
                ('DetailId', models.AutoField(primary_key=True)),
                ('EmissionsId', models.ForeignKey(
                    to='emissions.EmissionsData',
                    on_delete=models.CASCADE,
                    related_name='details',
                )),
                # Repeat tenant FK for middleware to filter line items directly
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='emissions_details',
                )),
                ('Description', models.CharField(max_length=200)),
                ('QuantityOrCost', models.DecimalField(max_digits=18, decimal_places=4)),
                ('Unit', models.CharField(max_length=50)),
                ('EmissionFactor', models.DecimalField(max_digits=18, decimal_places=8)),
                ('EmissionFactorSource', models.CharField(max_length=200)),
                ('Gas', models.CharField(max_length=50)),
                ('GasSubtype', models.CharField(max_length=50, null=True, blank=True)),
                ('GwpDatasetId', models.ForeignKey(
                    to='emissions.GwpDatasets',
                    on_delete=models.PROTECT,
                )),
                ('EmissionsAmount', models.DecimalField(
                    max_digits=18, decimal_places=4, null=True, blank=True,
                    help_text="Calculated server-side (kg CO2e)"
                )),
                ('EmissionsAmountTonnes', models.DecimalField(
                    max_digits=18, decimal_places=6, null=True, blank=True,
                )),
                ('Remarks', models.TextField(null=True, blank=True)),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'emissions_details'},
        ),

        # ── EmissionsOffsets ───────────────────────────────────────────────────
        # Carbon offsets linked to an emissions record (RECs, carbon credits etc.)
        migrations.CreateModel(
            name='EmissionsOffsets',
            fields=[
                ('OffsetId', models.AutoField(primary_key=True)),
                ('EmissionsId', models.ForeignKey(
                    to='emissions.EmissionsData',
                    on_delete=models.CASCADE,
                    related_name='offsets',
                )),
                ('EntityId', models.ForeignKey(
                    to='entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='emissions_offsets',
                )),
                ('Title', models.CharField(max_length=200)),
                ('OffsetType', models.CharField(
                    max_length=100,
                    help_text="e.g. Renewable Energy Certificate, Carbon Credit, REDD+"
                )),
                ('Provider', models.CharField(max_length=200)),
                ('CertificateNumber', models.CharField(max_length=100, blank=True, null=True)),
                ('OffsetAmountTonnes', models.DecimalField(
                    max_digits=18,
                    decimal_places=6,
                    help_text="Offset amount in tCO2e"
                )),
                ('ValidFrom', models.DateField(null=True, blank=True)),
                ('ValidTo', models.DateField(null=True, blank=True)),
                ('Remarks', models.TextField(null=True, blank=True)),
                # BaseAuditMixin
                ('Status', models.PositiveSmallIntegerField(default=1)),
                ('ApprovalStatus', models.PositiveSmallIntegerField(default=1)),
                ('DeletedAt', models.DateTimeField(null=True, blank=True)),
                ('CreatedAt', models.DateTimeField(auto_now_add=True)),
                ('UpdatedAt', models.DateTimeField(auto_now=True)),
                ('CreatedBy', models.IntegerField(null=True, blank=True)),
                ('UpdatedBy', models.IntegerField(null=True, blank=True)),
            ],
            options={'db_table': 'emissions_offsets'},
        ),

        # ── Indexes ────────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name='EmissionsData',
            index=models.Index(fields=['EntityId', 'ProjectId'], name='idx_emissions_entity_project'),
        ),
        migrations.AddIndex(
            model_name='EmissionsData',
            index=models.Index(fields=['EntityId', 'Scope'], name='idx_emissions_entity_scope'),
        ),
        migrations.AddIndex(
            model_name='EmissionsData',
            index=models.Index(fields=['VerificationStatus'], name='idx_emissions_verification'),
        ),
        migrations.AddIndex(
            model_name='EmissionsData',
            index=models.Index(
                fields=['ReportingPeriodFrom', 'ReportingPeriodTo'],
                name='idx_emissions_period',
            ),
        ),
    ]

"""
Migration: Targets and TargetMilestones
App: apps.emissions
Depends on: apps.entities, apps.users

Targets model the entity's project goals (hectares restored, tCO₂ sequestered/yr,
internal reduction targets, net-zero commitments).

Target types:
  AbsoluteContraction — reduce total emissions by X% vs base year
  IntensityBased — reduce emissions per unit of output (revenue, m², employee etc.)

Validation workflow:
  Internal → Submitted → Validated | Rejected
  Validated targets are immutable (same rule as verified EmissionsData).
  Only SuperAdmin can unlock a validated target.

TargetMilestones store interim checkpoints (e.g. 25% reduction by 2025,
50% by 2030, net zero by 2050) for progress tracking in reports.
"""

from django.db import migrations, models
import django.db.models.deletion


TARGET_TYPE_CHOICES = [
    (1, 'Absolute Contraction — reduce total GHG by X% vs base year'),
    (2, 'Intensity-Based — reduce GHG per unit of output'),
]

TARGET_FRAMEWORK_CHOICES = [
    (1, 'Internal target'),
    (2, 'Net Zero'),
    (3, 'Project / Credit goal'),
]

TARGET_VALIDATION_STATUS = [
    (1, 'Internal — set but not submitted for external validation'),
    (2, 'Submitted — submitted to validation body'),
    (3, 'Validated — externally approved'),
    (4, 'Rejected — validation failed'),
    (5, 'Expired — target period has passed without achievement'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
        ('emissions', '0022_ghg_inventories'),
    ]

    operations = [

        # ── Targets ────────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Targets',
            fields=[
                ('TargetId', models.AutoField(primary_key=True)),
                ('EntityId', models.ForeignKey(
                    'entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='targets',
                )),
                ('TargetName', models.CharField(max_length=200,
                    help_text="e.g. '50% Scope 1+2 reduction by 2030' or 'Restore 100 ha by 2035'"
                )),
                ('Framework', models.PositiveSmallIntegerField(choices=TARGET_FRAMEWORK_CHOICES)),
                ('TargetType', models.PositiveSmallIntegerField(choices=TARGET_TYPE_CHOICES)),
                # Which scopes this target covers (stored as JSON list: [1], [1,2], [1,2,3], [3])
                ('ScopesCovered', models.JSONField(
                    default=list,
                    help_text="List of scopes: e.g. [1, 2] or [1, 2, 3]."
                )),
                # Base year
                ('BaselineYear', models.PositiveSmallIntegerField(
                    help_text="Base year for percentage reduction calculations (4-digit year)"
                )),
                ('BaselineEmissionsTonnesCO2e', models.DecimalField(
                    max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text=(
                        "Total emissions in base year for the scopes covered. "
                        "Linked to GHGInventory for that year where possible."
                    )
                )),
                ('BaselineInventoryId', models.ForeignKey(
                    'emissions.GHGInventories',
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='baseline_targets',
                    help_text="GHGInventory record for the base year (preferred over manual BaselineEmissions entry)"
                )),
                # Target year and reduction
                ('TargetYear', models.PositiveSmallIntegerField(
                    help_text="Year by which the target must be achieved (4-digit year)"
                )),
                ('TargetReductionPercent', models.DecimalField(
                    max_digits=6, decimal_places=2,
                    null=True, blank=True,
                    help_text=(
                        "For AbsoluteContraction: % reduction vs base year. "
                        "e.g. 50.0 = 50% reduction."
                    )
                )),
                ('TargetEmissionsTonnesCO2e', models.DecimalField(
                    max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text=(
                        "Absolute target level in tCO2e = BaselineEmissions × (1 − TargetReductionPercent/100). "
                        "Server-computed from BaselineEmissions + TargetReductionPercent."
                    )
                )),
                # Intensity target fields (only for TargetType=3)
                ('IntensityMetric', models.CharField(max_length=100, null=True, blank=True,
                    help_text="Unit of intensity denominator: e.g. 'USD revenue', 'FTE', 'm² floor area', 'MWh produced'"
                )),
                ('BaselineIntensity', models.DecimalField(max_digits=14, decimal_places=6,
                    null=True, blank=True,
                    help_text="tCO2e per IntensityMetric unit in base year"
                )),
                ('TargetIntensity', models.DecimalField(max_digits=14, decimal_places=6,
                    null=True, blank=True,
                    help_text="tCO2e per IntensityMetric unit in target year"
                )),
                # Validation
                ('ValidationStatus', models.PositiveSmallIntegerField(
                    default=1,
                    choices=TARGET_VALIDATION_STATUS,
                )),
                ('ValidatedBy', models.CharField(max_length=200, null=True, blank=True,
                    help_text="External body name: e.g. 'Verra', 'Gold Standard'"
                )),
                ('ValidationReference', models.CharField(max_length=200, null=True, blank=True,
                    help_text="Validation certificate or reference number"
                )),
                ('ValidatedAt', models.DateTimeField(null=True, blank=True)),
                # Immutability — validated targets cannot be edited
                # Enforced at serializer layer; SuperAdmin can unlock via dedicated endpoint
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
            options={'db_table': 'targets'},
        ),

        # ── TargetMilestones ───────────────────────────────────────────────────
        migrations.CreateModel(
            name='TargetMilestones',
            fields=[
                ('MilestoneId', models.AutoField(primary_key=True)),
                ('TargetId', models.ForeignKey(
                    'emissions.Targets',
                    on_delete=models.CASCADE,
                    related_name='milestones',
                )),
                ('MilestoneYear', models.PositiveSmallIntegerField(
                    help_text="Interim checkpoint year"
                )),
                ('ExpectedReductionPercent', models.DecimalField(
                    max_digits=6, decimal_places=2,
                    null=True, blank=True,
                    help_text="Expected % reduction vs base year at this milestone"
                )),
                ('ExpectedEmissionsTonnesCO2e', models.DecimalField(
                    max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text="Absolute expected emissions level at this milestone (tCO2e)"
                )),
                ('ExpectedIntensity', models.DecimalField(
                    max_digits=14, decimal_places=6,
                    null=True, blank=True,
                    help_text="Expected intensity at this milestone (for intensity targets)"
                )),
                # Actual achieved values — populated when the milestone year's inventory is finalised
                ('ActualEmissionsTonnesCO2e', models.DecimalField(
                    max_digits=18, decimal_places=4,
                    null=True, blank=True,
                )),
                ('ActualInventoryId', models.ForeignKey(
                    'emissions.GHGInventories',
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='milestone_actuals',
                    help_text="GHGInventory for MilestoneYear — auto-links when inventory is finalised"
                )),
                ('AchievementStatus', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    help_text="1=OnTrack, 2=AtRisk, 3=Achieved, 4=Missed"
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
            options={'db_table': 'target_milestones'},
        ),

        migrations.AddIndex(
            model_name='Targets',
            index=models.Index(fields=['EntityId', 'Framework'], name='idx_target_entity_framework'),
        ),
        migrations.AddConstraint(
            model_name='TargetMilestones',
            constraint=models.UniqueConstraint(
                fields=['TargetId', 'MilestoneYear'],
                name='unique_milestone_per_target_year'
            ),
        ),
    ]

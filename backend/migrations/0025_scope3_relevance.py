"""
Migration: Scope3RelevanceAssessments
App: apps.emissions
Depends on: apps.entities, apps.users, emissions.0022_ghg_inventories

GHG Protocol Corporate Value Chain Standard (Scope 3) requires entities to:
  1. Identify all 15 Scope 3 categories
  2. Assess relevance of each category to their operations
  3. Document excluded categories with justification
  4. Re-assess when operations change significantly

This table stores that assessment per entity per reporting year.
Completing this assessment is a prerequisite for a GHG Protocol-conformant
Scope 3 inventory.

The 15 GHG Protocol Scope 3 categories:
  Upstream:
    1  Purchased Goods & Services
    2  Capital Goods
    3  Fuel & Energy Related (not in Scope 1 or 2)
    4  Upstream Transportation & Distribution
    5  Waste Generated in Operations
    6  Business Travel
    7  Employee Commuting
    8  Upstream Leased Assets
  Downstream:
    9  Downstream Transportation & Distribution
    10 Processing of Sold Products
    11 Use of Sold Products
    12 End-of-Life Treatment of Sold Products
    13 Downstream Leased Assets
    14 Franchises
    15 Investments
"""

from django.db import migrations, models

SCOPE3_CATEGORIES = [
    (1,  'Purchased Goods & Services'),
    (2,  'Capital Goods'),
    (3,  'Fuel & Energy Related Activities (not in Scope 1 or 2)'),
    (4,  'Upstream Transportation & Distribution'),
    (5,  'Waste Generated in Operations'),
    (6,  'Business Travel'),
    (7,  'Employee Commuting'),
    (8,  'Upstream Leased Assets'),
    (9,  'Downstream Transportation & Distribution'),
    (10, 'Processing of Sold Products'),
    (11, 'Use of Sold Products'),
    (12, 'End-of-Life Treatment of Sold Products'),
    (13, 'Downstream Leased Assets'),
    (14, 'Franchises'),
    (15, 'Investments'),
]

DATA_AVAILABILITY_CHOICES = [
    (1, 'Primary — direct measurement or supplier-specific data'),
    (2, 'Secondary — industry averages or published databases'),
    (3, 'Estimated — proxy data or spend-based calculation'),
    (4, 'Not Available — cannot currently obtain data'),
]

RELEVANCE_CRITERIA = [
    # GHG Protocol lists 5 criteria for relevance assessment
    # Each stored as a boolean; category is relevant if ANY criterion is met
    'Size — category likely to be large relative to total emissions',
    'Influence — entity has ability to influence GHG reductions in this category',
    'Risk — category contributes to entity\'s GHG-related risk exposure',
    'Stakeholders — key stakeholders expect this category to be included',
    'Outsourcing — category represents outsourced activities previously performed in-house',
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('users', '0001_users_roles'),
        ('emissions', '0022_ghg_inventories'),
    ]

    operations = [

        migrations.CreateModel(
            name='Scope3RelevanceAssessments',
            fields=[
                ('AssessmentId', models.AutoField(primary_key=True)),
                ('EntityId', models.ForeignKey(
                    'entities.Entities',
                    on_delete=models.PROTECT,
                    related_name='scope3_assessments',
                )),
                ('AssessmentYear', models.PositiveSmallIntegerField(
                    help_text="Reporting year this assessment applies to"
                )),
                ('InventoryId', models.ForeignKey(
                    'emissions.GHGInventories',
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='scope3_assessments',
                    help_text="Linked GHG inventory for this year (optional — links when inventory exists)"
                )),
                ('Category', models.PositiveSmallIntegerField(
                    choices=SCOPE3_CATEGORIES,
                    help_text="GHG Protocol Scope 3 category number (1–15)"
                )),
                ('IsRelevant', models.BooleanField(
                    help_text=(
                        "True if this category is material to the entity's operations. "
                        "GHG Protocol: relevant if any of the 5 relevance criteria are met."
                    )
                )),
                # GHG Protocol relevance criteria (store individually for transparency)
                ('CriteriaSize', models.BooleanField(
                    default=False,
                    help_text="Category likely to be large relative to total emissions"
                )),
                ('CriteriaInfluence', models.BooleanField(
                    default=False,
                    help_text="Entity has ability to influence GHG reductions in this category"
                )),
                ('CriteriaRisk', models.BooleanField(
                    default=False,
                    help_text="Category contributes to entity's GHG-related risk exposure"
                )),
                ('CriteriaStakeholders', models.BooleanField(
                    default=False,
                    help_text="Key stakeholders expect this category to be included"
                )),
                ('CriteriaOutsourcing', models.BooleanField(
                    default=False,
                    help_text="Category represents outsourced activities previously performed in-house"
                )),
                ('RelevanceRationale', models.TextField(
                    help_text=(
                        "Mandatory explanation. For relevant categories: why it is material. "
                        "For excluded categories: why it is not material (ExclusionReason also required)."
                    )
                )),
                ('ExclusionReason', models.TextField(
                    null=True, blank=True,
                    help_text=(
                        "Required when IsRelevant=False. Must explain why excluded. "
                        "GHG Protocol acceptable reasons: not applicable to operations, "
                        "not significant, data not available (temporary only)."
                    )
                )),
                ('DataAvailability', models.PositiveSmallIntegerField(
                    null=True, blank=True,
                    choices=DATA_AVAILABILITY_CHOICES,
                    help_text="Quality of data available for this category"
                )),
                # Estimated size used to justify relevance decision
                ('EstimatedEmissionsTonnesCO2e', models.DecimalField(
                    max_digits=18, decimal_places=4,
                    null=True, blank=True,
                    help_text=(
                        "Order-of-magnitude estimate used in relevance determination. "
                        "Not required to be precise — screening estimate is sufficient."
                    )
                )),
                ('EstimationMethod', models.TextField(
                    null=True, blank=True,
                    help_text="How EstimatedEmissions was calculated (spend-based, physical units, industry average)"
                )),
                ('AssessedBy', models.ForeignKey(
                    'users.Users',
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='scope3_assessments_made',
                )),
                ('LastReviewedAt', models.DateTimeField(auto_now=True)),
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
            options={'db_table': 'scope3_relevance_assessments'},
        ),

        # One assessment row per category per entity per year
        migrations.AddConstraint(
            model_name='Scope3RelevanceAssessments',
            constraint=models.UniqueConstraint(
                fields=['EntityId', 'AssessmentYear', 'Category'],
                name='unique_scope3_assessment_per_category_year'
            ),
        ),
        migrations.AddIndex(
            model_name='Scope3RelevanceAssessments',
            index=models.Index(
                fields=['EntityId', 'AssessmentYear'],
                name='idx_scope3_entity_year'
            ),
        ),
    ]

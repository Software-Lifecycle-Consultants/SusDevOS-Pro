"""
Migration: Entity consolidation approach + project partner share fields
App: apps.entities (ConsolidationApproach) + apps.projects (DevelopmentProjectPartners)
Depends on: entities.0001_entities, projects.0001_projects, emissions.0022_ghg_inventories

GHG Protocol Corporate Standard requires entities to declare a consolidation
approach — the boundary-setting rule used to determine which operations are
included in the inventory:

  1. Equity Share        — include % of emissions proportional to ownership share
  2. Financial Control   — include 100% of emissions where entity has financial control
  3. Operational Control — include 100% of emissions where entity has operational control

The approach is set at entity level (Entities.ConsolidationApproach) and can be
overridden per GHG inventory (GHGInventories.ConsolidationApproach).

=== DevelopmentProjectPartners: equity share fields ===

When multiple entities co-own or co-operate a project, emissions can be
double-counted if each entity reports 100% of the project's emissions.

For entities using the Equity Share approach, PartnerSharePercent stores the
ownership percentage so the reporting engine can attribute:
  AttributableEmissions = ProjectEmissions × (PartnerSharePercent / 100)

IsDoubleCountingRisk flags records where:
  - The same project appears in multiple entities' inventories
  - The consolidation approach differs between partners (one uses EquityShare,
    another uses OperationalControl)
  - Emissions may therefore be counted more than once across GHG inventories

DoubleCountingNotes documents the risk and any mitigation applied
(e.g. agreed exclusion, proportional allocation agreement).

This does NOT automatically deduplicate — it surfaces the risk so reviewers
and verifiers can make a judgment call. GHG Protocol Section 3.5 requires
disclosure of double-counting risks in the inventory report.
"""

from django.db import migrations, models

CONSOLIDATION_APPROACH_CHOICES = [
    (1, 'Equity Share — report % of emissions equal to equity ownership share'),
    (2, 'Financial Control — report 100% of emissions where financial control exists'),
    (3, 'Operational Control — report 100% of emissions where operational control exists'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('entities', '0001_entities'),
        ('projects', '0001_projects'),
        ('emissions', '0022_ghg_inventories'),
    ]

    operations = [

        # ── Entities: default consolidation approach ───────────────────────────
        migrations.AddField(
            model_name='Entities',
            name='ConsolidationApproach',
            field=models.PositiveSmallIntegerField(
                null=True,
                blank=True,
                choices=CONSOLIDATION_APPROACH_CHOICES,
                help_text=(
                    "GHG Protocol organisational boundary-setting approach. "
                    "Required before a GHG inventory can be marked as conformant. "
                    "Can be overridden per inventory in GHGInventories.ConsolidationApproach "
                    "if the approach changed mid-period."
                )
            ),
        ),

        # ── Entities: parent/subsidiary relationship flag ──────────────────────
        # Needed for Financial Control and Equity Share consolidation: entities
        # that are subsidiaries must be identifiable so the parent can include
        # or exclude their emissions appropriately.
        migrations.AddField(
            model_name='Entities',
            name='ParentEntityId',
            field=models.ForeignKey(
                'entities.Entities',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='subsidiaries',
                help_text=(
                    "Parent entity in a corporate group structure. "
                    "Used to resolve consolidation boundaries: "
                    "parent uses Financial/Operational Control → include 100% of subsidiary emissions; "
                    "parent uses Equity Share → include % per OwnershipSharePercent."
                )
            ),
        ),
        migrations.AddField(
            model_name='Entities',
            name='OwnershipSharePercent',
            field=models.DecimalField(
                max_digits=6,
                decimal_places=3,
                null=True,
                blank=True,
                help_text=(
                    "Parent entity's ownership share in this entity (0–100). "
                    "Used when ParentEntity uses Equity Share consolidation. "
                    "e.g. 60.000 = parent owns 60%, attributes 60% of this entity's emissions."
                )
            ),
        ),

        # ── DevelopmentProjectPartners: equity share + double-counting fields ──
        migrations.AddField(
            model_name='DevelopmentProjectPartners',
            name='PartnerSharePercent',
            field=models.DecimalField(
                max_digits=6,
                decimal_places=3,
                null=True,
                blank=True,
                help_text=(
                    "This entity's ownership/equity share in the project (0–100). "
                    "Used by reporting engine for Equity Share consolidation: "
                    "AttributableEmissions = ProjectEmissions × (PartnerSharePercent / 100). "
                    "All partner shares for a project should sum to 100; "
                    "enforced at application layer with a warning (not a DB constraint, "
                    "as minority interests and non-partner shares may exist)."
                )
            ),
        ),
        migrations.AddField(
            model_name='DevelopmentProjectPartners',
            name='PartnerConsolidationApproach',
            field=models.PositiveSmallIntegerField(
                null=True,
                blank=True,
                choices=CONSOLIDATION_APPROACH_CHOICES,
                help_text=(
                    "This partner's consolidation approach for this project. "
                    "Overrides the entity-level default for this specific project. "
                    "NULL = inherit from Entity.ConsolidationApproach."
                )
            ),
        ),
        migrations.AddField(
            model_name='DevelopmentProjectPartners',
            name='IsDoubleCountingRisk',
            field=models.BooleanField(
                default=False,
                help_text=(
                    "True if this project's emissions may be reported by more than one partner. "
                    "Flag is set automatically when: (a) multiple entities are partners, "
                    "AND (b) at least one uses OperationalControl or FinancialControl "
                    "(100% attribution) while others also include this project. "
                    "Requires disclosure in GHG inventory report per GHG Protocol §3.5."
                )
            ),
        ),
        migrations.AddField(
            model_name='DevelopmentProjectPartners',
            name='DoubleCountingNotes',
            field=models.TextField(
                null=True,
                blank=True,
                help_text=(
                    "Required when IsDoubleCountingRisk=True. "
                    "Document: which entities are both reporting this project, "
                    "what approach each uses, and what mitigation is applied "
                    "(e.g. agreed exclusion, proportional allocation agreement, disclosure only)."
                )
            ),
        ),

        # Index for quick lookups when computing partner-attributed emissions
        migrations.AddIndex(
            model_name='DevelopmentProjectPartners',
            index=models.Index(
                fields=['EntityId', 'ProjectId'],
                name='idx_project_partner_entity'
            ),
        ),
    ]

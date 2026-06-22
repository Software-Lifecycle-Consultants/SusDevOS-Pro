"""
Migration: Biomass Carbon Fields — Species, TreeRemovalRemovedSpecies, RestorationSpecies
App: apps.ecosystem + apps.restorations
Depends on: ecosystem.0001, restorations.0001

Adds IPCC-aligned biomass carbon calculation fields so that tree removals
and restorations can report carbon stock changes rather than using the generic
quantity × emission_factor formula (which does not apply to LULUCF accounting).

=== IPCC Tier 1 Carbon Stock Calculation for Tree Removals ===

Step 1: Above-ground biomass (AGB) per tree (tonnes dry matter)
  Using volume-based approach (when VolumeM3 is known):
    AGB = VolumeM3 × BasicWoodDensity × BiomassBiomasExpansionFactor

  Using DBH-based approach (when WidthAtBreastHeight is known — simplified):
    AGB = lookup from species-specific allometric table (Tier 2/3)
    For Tier 1: use IPCC Table 4.5 default BEFs by forest type

Step 2: Below-ground biomass (BGB)
  BGB = AGB × RootToShootRatio
  IPCC AR6 default R by forest type:
    Tropical: 0.37, Temperate: 0.26, Boreal: 0.23

Step 3: Total biomass
  TotalBiomass = (AGB + BGB) × Count

Step 4: Carbon stock
  CarbonStock = TotalBiomass × CarbonFraction
  IPCC default CarbonFraction = 0.47 for all forest types

Step 5: CO2 equivalent
  CO2Equivalent = CarbonStock × (44/12)   [molecular weight ratio CO2/C]

All calculated fields are server-populated (never trust client values).
BiomassCalculationMethod records which tier/approach was used — mandatory
for GHG inventory transparency.

=== Restoration Sequestration ===

Annual sequestration is species- and ecosystem-specific. This model stores:
- AnnualSequestrationRateTonnesCO2ePerHa: from literature/IPCC Annex 3A.1
- AreaHectares: area covered by this restoration planting
- CumulativeSequestrationTonnesCO2e: calculated as:
    AnnualRate × AreaHa × YearsEstablished × SurvivalEstimate × (1 − LeakageDiscountPct/100)

Permanence and additionality are flagged but not deducted automatically —
these require project-level assessment documented in RestorationNotes.
"""

from django.db import migrations, models
import django.db.models.deletion


BIOMASS_CALC_METHOD = [
    (1, 'IPCC Tier 1 — default BEF by forest type'),
    (2, 'IPCC Tier 2 — country-specific BEF'),
    (3, 'IPCC Tier 3 — measured / allometric equations'),
    (4, 'Manual entry — pre-calculated values provided directly'),
]

IPCC_FOREST_TYPE = [
    ('tropical',   'Tropical'),
    ('temperate',  'Temperate'),
    ('boreal',     'Boreal'),
    ('mangrove',   'Mangrove'),
    ('savanna',    'Savanna / Woodland'),
    ('shrubland',  'Shrubland'),
    ('grassland',  'Grassland'),
]

PERMANENCE_RISK = [
    (1, 'Low — legally protected, low disturbance risk'),
    (2, 'Medium — some disturbance risk (fire, pest, land tenure)'),
    (3, 'High — significant risk of reversal'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('ecosystem', '0001_ecosystem_species'),
        ('restorations', '0001_restorations'),
    ]

    operations = [

        # ── Species: IPCC biomass parameters ──────────────────────────────────
        migrations.AddField(
            model_name='Species',
            name='IPCCForestType',
            field=models.CharField(
                max_length=20, choices=IPCC_FOREST_TYPE,
                null=True, blank=True,
                help_text="IPCC forest type for Tier 1 BEF lookup"
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='BasicWoodDensity',
            field=models.DecimalField(
                max_digits=8, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "D — tonnes dry matter per m³ fresh volume. "
                    "IPCC Table 4.13 defaults by species group. "
                    "e.g. Tropical hardwood ~0.60, Tropical softwood ~0.45"
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='BiomassExpansionFactor',
            field=models.DecimalField(
                max_digits=8, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "BEF — converts net annual increment or merchantable volume "
                    "to total above-ground biomass. "
                    "IPCC Table 4.5 defaults: Tropical ~1.74, Temperate ~1.30, Boreal ~1.30"
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='RootToShootRatio',
            field=models.DecimalField(
                max_digits=8, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "R — below-ground to above-ground biomass ratio. "
                    "IPCC Table 4.4 defaults: Tropical 0.37, Temperate 0.26, Boreal 0.23"
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='CarbonFraction',
            field=models.DecimalField(
                max_digits=6, decimal_places=4,
                default=0.47,
                null=True, blank=True,
                help_text=(
                    "CF — carbon content of dry biomass as a fraction. "
                    "IPCC default 0.47 for all forest types. "
                    "Use species-specific value for Tier 2."
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='AnnualSequestrationRateTonnesCO2ePerHa',
            field=models.DecimalField(
                max_digits=10, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "Mean annual increment of CO2e sequestered per hectare at maturity. "
                    "Source: IPCC Annex 3A.1, national forest inventories, or peer-reviewed literature. "
                    "Used for restoration sequestration calculations."
                )
            ),
        ),
        migrations.AddField(
            model_name='Species',
            name='BiomassDataSource',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text="Citation for biomass parameter values (IPCC table ref, study DOI, etc.)"
            ),
        ),

        # ── TreeRemovalRemovedSpecies: carbon stock calculation fields ──────────
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='VolumeM3',
            field=models.DecimalField(
                max_digits=12, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "Merchantable timber volume in m³. Used in volume-based BEF approach "
                    "when DBH data is unavailable. Per-removal total (all trees)."
                )
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='BiomassCalculationMethod',
            field=models.PositiveSmallIntegerField(
                null=True, blank=True,
                choices=BIOMASS_CALC_METHOD,
                help_text="Which IPCC tier / approach was used to calculate carbon stock"
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='AboveGroundBiomassTonnes',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text="Calculated AGB in tonnes dry matter. Server-populated."
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='BelowGroundBiomassTonnes',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text="Calculated BGB = AGB × RootToShootRatio. Server-populated."
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='TotalBiomassTonnes',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text="AGB + BGB in tonnes dry matter. Server-populated."
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='CarbonStockTonnesC',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text="TotalBiomass × CarbonFraction in tonnes C. Server-populated."
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='CO2EquivalentTonnes',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "CarbonStockTonnesC × (44/12) = tCO2 released. "
                    "This is biogenic CO2 — reported as LULUCF emission, "
                    "NOT as Scope 1 fossil CO2 under GHG Protocol corporate standard. "
                    "Server-populated."
                )
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='DeadOrganicMatterTonnesCO2e',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "CO2e from dead organic matter (litter + deadwood) disturbed by removal. "
                    "Optional — Tier 2/3 only. Requires site-specific DOM carbon stock data."
                )
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='SoilCarbonTonnesCO2e',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "CO2e from soil organic carbon disturbance. "
                    "Optional — Tier 3 only. Requires soil carbon measurement."
                )
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='TotalCarbonStockLossTonnesCO2e',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "CO2EquivalentTonnes + DeadOrganicMatter + SoilCarbon. "
                    "Total LULUCF carbon stock loss for this species removal. Server-populated."
                )
            ),
        ),
        migrations.AddField(
            model_name='TreeRemovalRemovedSpecies',
            name='BiomassCalculationNotes',
            field=models.TextField(null=True, blank=True,
                help_text="Mandatory when BiomassCalculationMethod=4 (Manual) — document source"
            ),
        ),

        # ── RestorationSpecies: sequestration calculation fields ────────────────
        migrations.AddField(
            model_name='RestorationSpecies',
            name='AreaHectares',
            field=models.DecimalField(
                max_digits=12, decimal_places=4,
                null=True, blank=True,
                help_text="Area planted/restored with this species in hectares"
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='AnnualSequestrationRateTonnesCO2ePerHa',
            field=models.DecimalField(
                max_digits=10, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "Species-specific sequestration rate. Sourced from Species.AnnualSequestrationRateTonnesCO2ePerHa "
                    "by default, but can be overridden per restoration record for site-specific data."
                )
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='CumulativeSequestrationTonnesCO2e',
            field=models.DecimalField(
                max_digits=14, decimal_places=4,
                null=True, blank=True,
                help_text=(
                    "Calculated: AnnualRate × AreaHa × YearsEstablished × SurvivalEstimate "
                    "× (1 − LeakageDiscountPct/100). Server-populated."
                )
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='YearsEstablished',
            field=models.DecimalField(
                max_digits=6, decimal_places=2,
                null=True, blank=True,
                help_text="Years since EstablishedDate — computed from EstablishedDate to today at report time"
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='PermanenceRisk',
            field=models.PositiveSmallIntegerField(
                null=True, blank=True,
                choices=PERMANENCE_RISK,
                help_text="Risk that sequestered carbon will be released before the accounting period ends"
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='LeakageDiscountPercent',
            field=models.DecimalField(
                max_digits=5, decimal_places=2,
                default=0,
                null=True, blank=True,
                help_text=(
                    "% deduction applied to gross sequestration to account for leakage "
                    "(emissions displaced elsewhere by this restoration activity). "
                    "0–100. Typically 10–20% for community forestry per VCS methodology."
                )
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='AddionalityAssessment',
            field=models.TextField(
                null=True, blank=True,
                help_text=(
                    "Narrative assessment of additionality: would this restoration have occurred "
                    "without the project intervention? Required for carbon credit claims."
                )
            ),
        ),
        migrations.AddField(
            model_name='RestorationSpecies',
            name='SequestrationDataSource',
            field=models.CharField(
                max_length=200, null=True, blank=True,
                help_text="Citation for sequestration rate used (IPCC Annex, study DOI, national data)"
            ),
        ),
    ]

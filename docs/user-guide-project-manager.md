# SusDevOS Guide for Development Project Managers — Projects, Land Parcels, Ecosystem Tracking & Biodiversity

**Who this guide is for:** Development project managers and land managers responsible for tracking the environmental footprint of construction, infrastructure, or land development projects. You typically hold the **Manager** or **Staff** role. This guide covers the modules most relevant to your work: Projects, Land Parcels, Ecosystem, Tree Removals, and Restorations.

**What you can do:**
- Create and manage development projects and phases
- Map land parcels with GIS boundaries
- Record pre-development ecosystem and species surveys
- Log tree removals and calculate biomass carbon lost
- Track habitat restorations and carbon sequestration over time
- Link all of the above to your organisation's GHG inventory

---

## 1. Understanding How Projects Connect to Emissions

Every emissions record, land parcel, tree removal, and restoration in SusDevOS can be linked to a **Project**. This lets your sustainability manager slice the GHG inventory by project — essential for planning gain reporting, EIA commitments, and developer contributions.

The flow is:
```
Project → Phases → Land Parcels → [Ecosystem | Tree Removals | Restorations | Emissions Records]
```

You don't have to use all of these. A project with just emissions records is valid. But the more you link, the richer the project-level report.

---

## 2. Creating and Managing Development Projects

### 2.1 Create a project

1. Navigate to **Projects → New Project**.
2. Fill in:
   - **Project Name** — use the planning reference or site name for easy cross-referencing.
   - **Project Type** — Residential Development, Commercial Development, Infrastructure, Retrofit, Land Management, or Other.
   - **Status** — Pre-application, Planning, Under Construction, Operational, or Completed.
   - **Start Date / Expected Completion**.
   - **Planning Reference** — the LPA reference number (e.g. `22/01234/FUL`).
   - **Description** — a brief summary. Include site area and number of units if relevant.
3. Click **Create**.

### 2.2 Add project phases

Most developments move through distinct phases with different emission profiles (earthworks, substructure, superstructure, fit-out, operation). Breaking a project into phases lets you track emissions and biodiversity impacts over time.

1. Open the project and click **Phases → Add Phase**.
2. Name the phase (e.g. "Demolition", "Construction", "Handover") and set start/end dates.
3. When recording emissions or tree removals, you can select the Phase they belong to.

### 2.3 Link team members to a project

Projects don't have their own user permissions — all users in your entity can see all projects. To indicate ownership:
- Assign yourself or a colleague as **Project Lead** in the project details.
- Project Leads receive Celery-generated notifications when a linked inventory is verified or a restoration milestone is due.

---

## 3. Mapping Land Parcels

A **Land Parcel** represents a defined area of land involved in the project — a development site, a retained habitat, a mitigation area, or a biodiversity net gain receptor site.

> **GIS boundary mapping requires the Professional plan.** On Starter, you can record land parcels with address and area (hectares) but cannot draw polygon boundaries.

### 3.1 Create a land parcel

1. Navigate to **Land → New Land Parcel**.
2. Fill in:
   - **Parcel Name** — e.g. "Site A — Development Footprint" or "Receptor Site — Ancient Woodland Buffer".
   - **Land Use** — select from the IPCC LULUCF land use categories: Forest, Cropland, Grassland, Wetland, Settlement, Other Land.
   - **Area (ha)** — total area of the parcel.
   - **Parcel Type** — Development Site, Retained Habitat, Mitigation Area, Receptor Site, or Other.
   - **Project** — link to the project this parcel belongs to.
3. On Professional plan: click **Draw Boundary** on the map and trace the parcel boundary. The GIS polygon is stored in PostGIS and used in ecosystem and IPCC biomass calculations.
4. Click **Save**.

### 3.2 Land use change tracking

If a parcel's land use changes during the project (e.g. grassland converted to settlement), record both the before and after states:

1. Open the Land Parcel and scroll to **Land Use History**.
2. Click **Record Land Use Change**.
3. Enter the new land use and the date of change.

This history feeds into IPCC LULUCF biomass carbon calculations (see §5).

---

## 4. Ecosystem and Species Surveys

Before breaking ground, most major developments require a pre-development ecological survey. Record the results in SusDevOS to establish the baseline for biodiversity net gain and TNFD disclosure.

### 4.1 Create an ecosystem record

An **Ecosystem** record represents a distinct habitat area (e.g. ancient semi-natural woodland, lowland grassland, urban amenity grassland).

1. Navigate to **Ecosystem → New Ecosystem**.
2. Fill in:
   - **Ecosystem Name** — e.g. "Semi-improved Neutral Grassland — North Field".
   - **Habitat Type** — select from the UK Habitat Classification types.
   - **Area (ha)** — as mapped in the ecological survey.
   - **Condition** — Poor, Moderate, Good, or Excellent (aligns with BNG metric).
   - **Land Parcel** — link to the parcel this habitat is within.
   - **Survey Date** — date of the ecological survey.
3. Click **Save**.

### 4.2 Record species

For each ecosystem, record the species present from the ecological survey:

1. Open the Ecosystem record and click **Species → Add Species**.
2. Search by common name or scientific name. SusDevOS integrates with the GBIF taxonomy and the IUCN Red List, so searching "barn owl" returns `Tyto alba` with its IUCN conservation status pre-filled.
3. Enter:
   - **Count or Density** — number of individuals, breeding pairs, or density (per ha).
   - **Survey Method** — Walked Transect, Point Count, Camera Trap, etc.
   - **Confidence** — High, Medium, or Low.
4. Click **Save**.

Species with IUCN status Vulnerable, Endangered, or Critically Endangered are highlighted in red in the ecosystem summary. These are flagged for TNFD disclosure.

---

## 5. Recording Tree Removals and Biomass Carbon

Tree removals are one of the most significant biodiversity and carbon impacts of development. SusDevOS calculates the biomass carbon lost using IPCC Tier 1 (global default values) or Tier 2/3 methods (country/species-specific allometrics).

> **Tier 2/3 biomass calculations require Professional plan.** Starter uses Tier 1 IPCC defaults.

### 5.1 Record a tree removal

1. Navigate to **Restorations → Tree Removals → New Tree Removal**.
2. Fill in:
   - **Species** — search by common or scientific name.
   - **Diameter at Breast Height (DBH)** — in centimetres. Required for Tier 2 allometric equations.
   - **Height** — in metres (estimated or surveyed).
   - **Canopy Spread** — in metres (for area-based calculations).
   - **Health Status** — Healthy, Minor Decline, Major Decline, Dead.
   - **Removal Reason** — Development Clearance, Safety, Disease, or Other.
   - **Land Parcel** — link to the parcel the tree is on.
   - **Project Phase** — link to the project phase when removal occurs.
   - **Removal Date** — actual or planned date.
3. Click **Save**. SusDevOS calculates:
   - **Above-ground biomass carbon (tCO₂e)**
   - **Below-ground biomass carbon (tCO₂e)**
   - **Total carbon stock lost**

The calculation uses the IPCC Tier 1 equation:
```
Biomass (tonnes dry matter) = exp(a + b × ln(DBH))
Carbon stock = Biomass × carbon fraction (0.47 default, IPCC)
CO₂e = Carbon stock × 3.664 (molecular weight ratio CO₂/C)
```

> Note: Biogenic CO₂ from cleared trees is reported separately from the operational GHG inventory. It appears in the **Biogenic CO₂** column of your inventory report, not in the GWP total.

### 5.2 Bulk tree schedule import

If your arboricultural report includes a schedule of trees (typically hundreds of rows), use the CSV import:

1. Navigate to **Restorations → Tree Removals → Import**.
2. Download the tree schedule template.
3. Map your arboricultural survey columns to the template fields.
4. Upload. Each tree generates its own biomass carbon calculation on import.

---

## 6. Tracking Habitat Restorations

Restorations offset some of the biodiversity and carbon impact of development. SusDevOS tracks carbon sequestration over time using IPCC LULUCF growth curves.

### 6.1 Create a restoration record

1. Navigate to **Restorations → New Restoration**.
2. Fill in:
   - **Restoration Type** — Woodland Creation, Hedgerow Planting, Grassland Restoration, Wetland Creation, Green Roof, or Other.
   - **Area (ha)** — area being restored.
   - **Species Mix** — the planting species and proportions.
   - **Land Parcel** — the receptor site land parcel.
   - **Start Date** — when planting/seeding takes place.
   - **Target Condition** — the habitat condition this restoration aims to achieve (for BNG metric).
   - **Sequestration Method** — Tier 1 (IPCC defaults) or Tier 2/3 (species/country-specific).
3. Click **Save**.

### 6.2 Sequestration projections

SusDevOS generates a 30-year sequestration curve for the restoration, based on IPCC growth rates for the habitat type and climate zone.

Navigate to **Restorations → [restoration] → Sequestration Projection**. The chart shows:
- Annual CO₂e sequestered (tCO₂e/year)
- Cumulative carbon stock (tCO₂e over 30 years)
- Break-even point (year when cumulative sequestration exceeds carbon lost from tree removals)

This is useful for planning gain negotiations: you can show the Local Planning Authority when the biodiversity net gain receptor site will have recovered the carbon lost during construction.

### 6.3 Annual condition updates

Restoration success requires monitoring. Record annual condition surveys:

1. Open the restoration → **Monitoring Records → New Survey**.
2. Enter:
   - **Survey Date**
   - **Establishment Rate** — percentage of planted species that have survived.
   - **Actual Condition** — current habitat condition score.
   - **Notes** — any failures, pest damage, supplementary planting.

The sequestration projection updates based on actual establishment rates. If survival is below 70%, SusDevOS flags the restoration as "At Risk" and notifies the project lead.

---

## 7. Project-Level Carbon Reporting

Once projects, land parcels, tree removals, restorations, and emissions are all linked, you can generate a project-level carbon summary.

1. Navigate to **Projects → [project] → Carbon Summary**.
2. The summary shows:
   - **Construction emissions** (Scope 1+3 from linked emissions records)
   - **Biomass carbon lost** (from tree removals)
   - **Sequestration** (from linked restorations, projected 30 years)
   - **Net project carbon** = construction emissions + biomass lost − sequestration

3. Navigate to **Reports → New Report → Project Carbon Summary** to generate a PDF.

This report is commonly used for:
- Planning applications (EIA carbon chapter evidence)
- Developer contribution negotiations (planning gain offset schemes)
- Net zero aligned design reviews

---

## 8. TNFD-Aligned Disclosure

On Professional plan and above, SusDevOS supports Taskforce on Nature-related Financial Disclosures (TNFD) aligned reporting.

TNFD requires disclosure of:
- Nature-related dependencies (what does the project depend on from nature?)
- Nature-related impacts (what does the project do to nature?)
- Nature-related risks (what regulatory or reputational risks arise?)

SusDevOS maps your ecosystem records, species records, and land use changes to the TNFD LOCATE–EVALUATE–ASSESS–PREPARE (LEAP) framework automatically.

1. Navigate to **Reports → TNFD Report**.
2. Select the project(s) to include.
3. Review the pre-populated LEAP disclosure table.
4. Add narrative in the free-text fields.
5. Generate PDF.

---

## 9. Quick Reference — Project Setup Checklist

Use this when starting a new development project:

- [ ] Project created with planning reference and status
- [ ] Project phases added (at minimum: Pre-construction, Construction, Operational)
- [ ] Land parcels created (development footprint + any mitigation/receptor sites)
- [ ] GIS boundaries drawn (Professional plan)
- [ ] Pre-development ecosystem surveys recorded
- [ ] Species records added for protected/notable species
- [ ] Tree schedule imported or entered individually
- [ ] Receptor site restorations created with planting spec
- [ ] Construction emissions records linked to project and phase
- [ ] Carbon summary reviewed and shared with sustainability manager

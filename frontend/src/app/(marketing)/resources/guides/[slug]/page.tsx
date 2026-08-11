import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Clock } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// ─────────────────────────────────────────────────────────────────────────────
// Guide content
// ─────────────────────────────────────────────────────────────────────────────

interface Guide {
  slug: string;
  title: string;
  description: string;
  badge: string;
  time: string;
  body: string;
}

const GUIDES: Guide[] = [
  {
    slug: "recording-ghg-emissions",
    badge: "GHG Emissions",
    time: "8 min read",
    title: "Recording GHG Emissions (Scope 1, 2, 3)",
    description:
      "How to log activity data, choose the right emission factor, and let SusDevOS calculate your tCO₂e — across all three scopes and all 15 Scope 3 categories.",
    body: `
## Overview

SusDevOS calculates all GHG emissions server-side. You enter the **activity quantity** (kWh, litres, km, £ spend, etc.) and SusDevOS multiplies it by the correct emission factor and GWP value to produce a tCO₂e figure. You never enter a CO₂e value directly — if you do, it will be overwritten on save.

The formula is:

\`\`\`
Emissions (kg CO₂e) = Quantity × Emission Factor × GWP₁₀₀
\`\`\`

---

## Creating an Emissions Record

1. Navigate to **Emissions → Records** and click **New Record**.
2. Set the **Scope** (1, 2, or 3).
3. Select a **Reporting Period** — this links the record to an open GHG Inventory.
4. Choose an **Emission Factor** from the library (DEFRA, EPA, or Climatiq).
5. Enter the **Quantity** and select the **Unit**. SusDevOS converts to canonical units automatically before applying the factor.
6. (Optional) Link the record to a **Project** or **Land Parcel**.
7. Click **Save**. The tCO₂e figure appears immediately.

---

## Scope 1 — Direct Emissions

Scope 1 covers emissions from sources owned or controlled by your organisation:

| Source | Unit to enter |
|---|---|
| Natural gas (boilers, furnaces) | kWh or m³ |
| Company vehicles (petrol, diesel) | litres or km |
| Refrigerant top-ups (HFCs) | kg of refrigerant |
| Biomass combustion | tonnes of fuel |

> **Biogenic CO₂:** If your Scope 1 includes biomass combustion, the biogenic CO₂ is calculated separately in \`BiogenicCO₂AmountTonnes\`. It does **not** appear in your GWP total — this is correct GHG Protocol behaviour. It is disclosed separately in your inventory report.

---

## Scope 2 — Purchased Electricity, Heat, Steam

Scope 2 always produces **two numbers**: location-based and market-based. See the [Scope 2 Dual Method guide](/resources/guides/scope-2-dual-method) for the full explanation.

To record Scope 2:

1. Set **Scope = 2** and select the **Electricity** subcategory.
2. Enter kWh consumed.
3. If you hold energy attribute certificates (REGOs, GOs, RECs), set the market-based emission factor to \`0\` or select your supplier's certified tariff.
4. Both figures are calculated and stored automatically.

---

## Scope 3 — Value Chain (all 15 categories)

SusDevOS supports all 15 Scope 3 categories from the GHG Protocol Corporate Value Chain Standard. Common ones:

| Category | Typical input |
|---|---|
| 1 — Purchased goods & services | £ spend or tonnes of material |
| 3 — Fuel- and energy-related | kWh or litres (upstream factor applied) |
| 4 — Upstream transportation | tonne-km or £ spend |
| 6 — Business travel | km by mode or £ spend |
| 11 — Use of sold products | kWh or units sold × in-use factor |
| 15 — Investments | £ invested × EXIOBASE factor |

For **spend-based** Scope 3 categories, SusDevOS converts your spend to USD using the daily ECB exchange rate before applying the EXIOBASE factor. The exchange rate used is stored on every record for audit.

---

## Choosing an Emission Factor

Open the **Emission Factors** library (sidebar → Emission Factors) to browse and search. Factors are organised by:

- **Source** (DEFRA, EPA, Climatiq)
- **Category** (fuel, electricity, transport, waste, etc.)
- **Unit** (kWh, litres, km, £, kg, etc.)

If you can't find the right factor in the library, use the Climatiq integration to search the Climatiq database directly from **Settings → Integrations**.

---

## GWP Dataset

By default, SusDevOS uses **IPCC AR6 GWP100** values. You can switch to AR5 or AR4 in **Settings → Calculation Settings** if required by your reporting framework. Changing the dataset applies to all new calculations; existing records retain their original GWP until explicitly recalculated.
    `.trim(),
  },

  {
    slug: "scope-2-dual-method",
    badge: "GHG Emissions",
    time: "5 min read",
    title: "Scope 2 Dual Method: Location-Based vs Market-Based",
    description:
      "Understand why both methods are required, when each applies, and how SusDevOS calculates both simultaneously for every electricity record.",
    body: `
## Why Two Methods?

The GHG Protocol Scope 2 Guidance (2015) requires organisations to calculate and disclose **both** methods separately. You may not choose one and omit the other.

| Method | What it measures | Emission factor used |
|---|---|---|
| **Location-based** | Average emissions intensity of the regional/national electricity grid | Grid average EF (e.g. UK national grid: ~0.207 kg CO₂e/kWh) |
| **Market-based** | Emissions from your contracted electricity supply | Supplier-specific EF or energy attribute certificate (EAC) factor |

The market-based figure reflects voluntary renewable electricity purchases (REGOs, GOs, RECs). If you hold certificates for 100% renewable supply, your market-based Scope 2 can be zero.

---

## How SusDevOS Calculates Both

Every time you save a Scope 2 emissions record, SusDevOS stores two separate values:

- \`EmissionsAmountLocationBased\` — calculated using the grid average factor for your entity's country
- \`EmissionsAmountMarketBased\` — calculated using the supplier or EAC factor you supply

Neither value overwrites the other. Both are displayed in the record and included in inventory reports.

---

## Setting Up Your Entity's Grid Factor

SusDevOS uses national grid emission factors (from DEFRA for UK entities, EPA eGRID for US, and Climatiq for others). The factor is applied automatically based on your entity's country setting.

To change or override the grid factor: **Settings → Entity → Electricity Grid Factor**.

---

## Recording a Scope 2 Entry

1. Go to **Emissions → Records → New Record**.
2. Set **Scope = 2**.
3. Enter the kWh consumed.
4. For the **market-based factor**:
   - If you hold REGOs/GOs/RECs for this supply: select the zero-carbon tariff or enter \`0\`.
   - If you have a supplier-specific declaration: enter the declared factor in kg CO₂e/kWh.
   - If you have no contractual instrument: SusDevOS uses the residual mix factor (same as location-based, or your country's published residual mix).
5. Save. Both figures are calculated instantly.

---

## In Reports

Your GHG Protocol PDF report and CSV export include both figures with clear labelling. Most voluntary reporting frameworks ask for market-based as the "primary" Scope 2 total, with location-based disclosed in a supplementary table.
    `.trim(),
  },

  {
    slug: "ghg-inventories",
    badge: "Inventories",
    time: "10 min read",
    title: "Building and Verifying a GHG Inventory",
    description:
      "Create a formal annual inventory, add emissions records, move through the verification workflow, and generate a GHG Protocol-conformant PDF report.",
    body: `
## What is a GHG Inventory?

A GHG Inventory in SusDevOS is a formal, versioned record that groups all emissions data for a single reporting year. Once an inventory reaches **Verified** status, it becomes immutable — no edits are allowed without creating a new version.

---

## Step 1: Create the Inventory

1. Navigate to **Emissions → Inventories → New Inventory**.
2. Fill in:
   - **Reporting Year** — the calendar or fiscal year (e.g. 2024).
   - **Base Year** — the baseline year used for target-setting. Usually the first year with complete data.
   - **Consolidation Approach** — must match your entity setting: Equity Share, Financial Control, or Operational Control.
   - **Boundary Notes** — describe inclusions and exclusions (e.g. "UK operations only; excludes leased vehicles below 3.5t").
3. Click **Create**. The inventory is created with \`VerificationStatus = 0\` (Draft).

---

## Step 2: Add Emissions Records

With the inventory open, records created in the same reporting period are automatically associated with it. You can also manually link a record to an inventory from the record's detail view.

Work through each scope:

- **Scope 1** — direct combustion, vehicles, refrigerants. See the [Emissions Recording guide](/resources/guides/recording-ghg-emissions).
- **Scope 2** — purchased electricity (both methods). See the [Scope 2 guide](/resources/guides/scope-2-dual-method).
- **Scope 3** — value chain categories relevant to your organisation. Document your relevance assessment (required for GHG Protocol conformance).

---

## Step 3: Review Totals

The inventory overview shows:

- Scope 1, 2 (location and market-based), and 3 totals in tCO₂e
- Per-category breakdown for Scope 3
- Biogenic CO₂ (separately, not in GWP total)
- Data completeness indicator

---

## Step 4: Internal Review and Approval

Move the inventory through the verification workflow:

| Status | Meaning |
|---|---|
| \`0 — Draft\` | Active data entry; edits allowed |
| \`1 — In Review\` | Internal review underway |
| \`2 — Approved\` | Internal sign-off complete |
| \`3 — Verified\` | Third-party verification; **immutable** |

To advance the status: open the inventory and click **Submit for Review**, then **Approve**, then **Mark Verified** (requires Manager or Admin role). Each state change is logged with the user's identity and timestamp.

> **Important:** Once \`VerificationStatus ≥ 3\`, the API rejects any edit to the inventory or its associated records with HTTP 403. This is intentional and cannot be overridden.

---

## Step 5: Generate the PDF Report

1. Open the verified inventory.
2. Click **Generate Report → PDF**.
3. SusDevOS produces a report containing:
   - Reporting entity, year, and boundary
   - Consolidation approach and boundary notes
   - Emission factor sources and GWP dataset used
   - Scope 1, 2, and 3 totals with subcategory breakdown
   - Biogenic CO₂ disclosure
   - Data quality assessment

Reports are stored in **Reports → My Reports** and available for download at any time.

---

## Bulk Import

To import many records at once: **Emissions → Records → Import**. Download the Excel template, fill in activity data, and upload. Validation errors are reported row-by-row before any data is committed.
    `.trim(),
  },

  {
    slug: "land-parcels-ecosystem",
    badge: "Land & Nature",
    time: "6 min read",
    title: "Land Parcels and Ecosystem Tracking",
    description:
      "Record precise GeoJSON boundaries, link parcels to development projects, log habitat types, and track ecosystem changes across your portfolio.",
    body: `
## Overview

Land parcels are the foundation of nature-related accounting in SusDevOS. Every tree removal, restoration activity, species record, and ecosystem metric is linked to a land parcel. Getting your parcel boundaries right first makes everything else easier.

---

## Creating a Land Parcel

1. Navigate to **Land Parcels → New Parcel**.
2. Enter:
   - **Name** and **Description**
   - **Area (hectares)** — the total parcel area
   - **Boundary** — paste a GeoJSON Polygon or MultiPolygon, or draw on the interactive map
   - **Country and Region** — used for grid emission factor lookup and GBIF species range queries
   - **Ecosystem Type** — woodland, grassland, wetland, heathland, arable, urban green space, etc.
3. Optionally link to a **Project**.
4. Save. The boundary is stored in PostGIS and displayed on an OpenStreetMap layer.

---

## Linking Parcels to Projects

Development projects in SusDevOS represent discrete activities (a housing development, road scheme, habitat creation scheme). Multiple land parcels can be linked to one project.

To link: open a project → **Land Parcels → Add Parcel**, or open a parcel → **Projects → Link Project**.

---

## Ecosystem Records

For each land parcel you can record:

| Field | What it captures |
|---|---|
| Habitat type | Broad habitat classification (EUNIS, UK NVC, etc.) |
| Area affected (ha) | Area impacted by the development or restoration |
| Condition | Poor / Moderate / Good / Excellent |
| Description | Free text — notes on current state, interventions planned |

Ecosystem records feed the TNFD LEAP biodiversity assessment. See the [TNFD guide](/resources/guides/tnfd-biodiversity) for the full workflow.

---

## Tree Removals

Tree removals are recorded per land parcel. SusDevOS uses IPCC Tier 1/2/3 biomass tables to calculate the carbon stock released. See the [Biomass Carbon guide](/resources/guides/biomass-carbon-tree-removals) for full details.

Navigate to **Land Parcels → [Parcel] → Tree Removals → Add Removal**.

---

## Restorations

Restoration activities (habitat creation, rewilding, reforestation) are also linked to land parcels. SusDevOS projects 30-year carbon sequestration curves based on IPCC growth parameters.

Navigate to **Restorations → New Restoration** and select the land parcel.
    `.trim(),
  },

  {
    slug: "biomass-carbon-tree-removals",
    badge: "Land & Nature",
    time: "7 min read",
    title: "Biomass Carbon and Tree Removals (IPCC LULUCF)",
    description:
      "How SusDevOS uses IPCC Tier 1/2/3 biomass tables to calculate carbon stock loss from tree removals and 30-year sequestration projections for restoration activities.",
    body: `
## The Science Behind the Numbers

SusDevOS implements IPCC 2006 LULUCF Guidelines for biomass carbon stock estimation. For tree removals, the calculation estimates the carbon locked in above-ground and below-ground biomass that is released (or transferred to harvested wood products) when trees are felled.

The core formula is:

\`\`\`
Carbon stock (tC) = Volume (m³) × Basic Wood Density (t/m³) × Biomass Expansion Factor × (1 + Root:Shoot Ratio)
\`\`\`

All species parameters (basic wood density, BEF, R:S ratio) are pulled from the GBIF taxonomy and IPCC Annex tables automatically when you select a species.

---

## Recording a Tree Removal

1. Navigate to **Land Parcels → [Parcel] → Tree Removals → Add Removal**.
2. Enter:
   - **Species** — start typing the common or scientific name; SusDevOS queries GBIF to confirm taxonomy and retrieve biomass parameters.
   - **Number of trees** (or stem count)
   - **Diameter at breast height (DBH)** — in cm; used with the allometric equation to estimate volume
   - **Height** (optional, improves accuracy)
   - **Removal reason** — development, disease, management, etc.
3. Save. SusDevOS calculates:
   - Above-ground biomass carbon (tC)
   - Below-ground biomass carbon (tC) using root:shoot ratio
   - Total carbon stock (tC) and CO₂e equivalent

---

## IPCC Tier Levels

| Tier | Method | When to use |
|---|---|---|
| Tier 1 | Default IPCC table values for the forest type | Adequate for most planning and EIA purposes |
| Tier 2 | Country-specific biomass parameters | Required for national GHG inventories |
| Tier 3 | Site-specific allometric equations | High-value sites or scientific-grade accounting |

SusDevOS defaults to Tier 1 for most species. If you have site-specific allometric data, you can enter custom parameters when creating the removal record.

---

## Restoration Sequestration Projections

For habitat restoration and reforestation projects, SusDevOS projects cumulative carbon sequestration over 30 years using IPCC growth curve parameters.

To create a restoration:
1. Go to **Restorations → New Restoration**.
2. Select the land parcel and enter the restored area in hectares.
3. Select the **restoration type** (broadleaf woodland, mixed woodland, grassland, wetland, heathland, etc.).
4. SusDevOS generates an annual sequestration schedule and cumulative tCO₂e chart.

The projections appear in project carbon summary reports and feed into net carbon balance calculations (removals minus sequestration).

---

## Where These Figures Appear

- **Land Parcels → [Parcel]** — carbon balance summary for the parcel
- **Projects → [Project]** — aggregate carbon across all linked parcels
- **Reports → Project Carbon Report** — suitable for planning consents, EIAs, and green finance documentation
    `.trim(),
  },

  {
    slug: "carbon-offsets-validation",
    badge: "Carbon Credits",
    time: "5 min read",
    title: "Carbon Offsets and Verra/Gold Standard Validation",
    description:
      "Log VCS and Gold Standard carbon credits, validate serial numbers against the live registries, and understand how validated credits affect your net inventory total.",
    body: `
## Overview

Carbon offsets in SusDevOS represent purchased carbon credits intended to compensate for residual emissions. SusDevOS validates serial numbers against the **Verra VCS** and **Gold Standard** registries in real time. Unvalidated credits are never deducted from your net inventory total.

---

## Adding a Carbon Offset

1. Navigate to **Offsets → New Offset**.
2. Enter:
   - **Registry** — Verra VCS or Gold Standard
   - **Serial Number** — the credit serial number from the registry certificate
   - **Vintage Year** — the year the emission reduction occurred
   - **Volume (tCO₂e)** — credits purchased
   - **Project Name** — the underlying project name (e.g. "Kariba REDD+ Forest Protection")
3. Click **Save & Validate**. SusDevOS queries the registry API and returns:
   - ✓ **Validated** — credit confirmed as issued and not previously retired
   - ✗ **Invalid** — serial number not found or already retired

---

## Validation Rules

| Status | Effect on inventory |
|---|---|
| Validated | Deducted from gross inventory total in reports |
| Pending | Shown but **not** deducted |
| Invalid | Flagged; **not** deducted; requires correction |

This rule is enforced server-side and cannot be overridden from the frontend.

---

## Viewing Your Offset Portfolio

**Offsets** (sidebar) shows:

- All credits with validation status
- Total validated tCO₂e
- Credits by vintage year and project type
- A breakdown of Verra vs Gold Standard credits

---

## How Offsets Appear in Reports

Your GHG Protocol PDF report includes:

- **Gross emissions** — total before offsets
- **Validated offsets** — total verified credits
- **Net emissions** — gross minus validated offsets

The GHG Protocol does not allow offsets to reduce Scope 1/2/3 figures — they are disclosed separately as compensation, not as a reduction to the emission totals themselves.

---

## Re-validating Credits

Validation status can change if a credit is subsequently retired by another buyer. Click **Re-validate** on any offset record to recheck the registry. Automated nightly re-validation runs on all pending and validated credits.
    `.trim(),
  },

  {
    slug: "tnfd-biodiversity",
    badge: "Biodiversity",
    time: "7 min read",
    title: "TNFD Biodiversity Reporting and Species Tracking",
    description:
      "Use the TNFD LEAP framework to structure biodiversity impact assessments, track species with IUCN Red List status, and generate TNFD-aligned disclosures.",
    body: `
## What is TNFD?

The Taskforce on Nature-related Financial Disclosures (TNFD) provides a framework for organisations to assess and disclose nature-related risks and dependencies. SusDevOS supports **TNFD v1.0** through its land, ecosystem, and species data models.

---

## The LEAP Approach

TNFD's recommended assessment process is LEAP: **Locate, Evaluate, Assess, Prepare**.

| Phase | What you do | SusDevOS feature |
|---|---|---|
| **Locate** | Identify where your operations interface with nature | Land parcel map and ecosystem records |
| **Evaluate** | Assess dependencies and impacts on ecosystems | Ecosystem condition records, biomass carbon calculations |
| **Assess** | Identify material nature-related risks and opportunities | Species records with IUCN status, restoration projections |
| **Prepare** | Respond, report, and disclose | Project carbon and biodiversity reports |

---

## Recording Species

1. Navigate to **Ecosystem → Species → Add Species Record**.
2. Enter the **species name** — SusDevOS queries **GBIF** to confirm taxonomy (kingdom, phylum, class, order, family, genus, species).
3. SusDevOS automatically fetches the **IUCN Red List status**:
   - Least Concern (LC)
   - Near Threatened (NT)
   - Vulnerable (VU)
   - Endangered (EN)
   - Critically Endangered (CR)
   - Extinct in the Wild (EW)
   - Extinct (EX)
4. Link the record to a **Land Parcel** and optionally a **Project**.
5. Enter observation details: date, count/abundance, observation method.

---

## Ecosystem Records

Alongside species, record the overall ecosystem state for each land parcel:

- **Habitat type** — use a recognised classification (EUNIS, UK BAP broad habitats)
- **Area (ha)** — affected or assessed area
- **Condition** — Poor / Moderate / Good / Excellent
- **Notes** — survey methodology, data sources, uncertainty

---

## Biodiversity Sensitivity

SusDevOS automatically flags land parcels that fall within or near:

- Protected areas (via GBIF/IUCN PA database)
- Key Biodiversity Areas (KBAs)
- Ramsar wetland sites

These flags appear on the parcel detail page and in biodiversity reports.

---

## Generating a Biodiversity Report

1. Navigate to **Reports → New Report → Biodiversity (TNFD)**.
2. Select the **Project** or individual **Land Parcels**.
3. SusDevOS generates a report including:
   - Parcel boundaries and ecosystem types
   - Species list with IUCN Red List status
   - Habitat condition assessments
   - Carbon stock (from any linked tree removals)
   - Restoration sequestration projections
   - LEAP phase narrative fields (editable)

The report is suitable for inclusion in TNFD-aligned annual reports and Environmental Impact Assessments.
    `.trim(),
  },

  {
    slug: "targets-milestones",
    badge: "Targets",
    time: "4 min read",
    title: "Setting Targets and Tracking Milestones",
    description:
      "Create emissions reduction or sequestration targets, add interim milestones, and track progress against baseline figures from your verified inventories.",
    body: `
## Overview

Targets in SusDevOS represent commitments to reduce emissions or increase sequestration over time. Each target has a **baseline year**, a **target year**, a **reduction percentage** (for emissions targets) or **sequestration amount** (for nature-based targets), and a set of **milestones** that break the journey into measurable steps.

---

## Creating a Target

1. Navigate to **Targets → New Target**.
2. Fill in:
   - **Name** — a short descriptive label (e.g. "Net zero by 2040")
   - **Type** — Absolute reduction, Intensity reduction, or Sequestration
   - **Baseline Year** — should match a verified GHG inventory year
   - **Baseline Value** — tCO₂e from the baseline inventory (auto-populated if you select an inventory)
   - **Target Year** — the year by which the target must be achieved
   - **Reduction / Sequestration %** — the percentage change from baseline
3. Click **Create**.

---

## Adding Milestones

Milestones are interim checkpoints on the way to the target. Each milestone has:

- **Year** — the checkpoint year
- **Expected Value** — expected tCO₂e at this point (calculated from the target trajectory, or entered manually)
- **Notes** — e.g. "Complete Scope 3 category 1 reduction programme"

To add: open a target → **Milestones → Add Milestone**.

---

## Tracking Progress

The target detail view shows:

- A trajectory chart from baseline to target year, with actual inventory totals overlaid
- Each milestone with status: **On track** / **At risk** / **Missed** / **Achieved**
- The current year's variance from the expected trajectory

SusDevOS compares each milestone year against the verified inventory total for that year (if available). If no verified inventory exists yet, the milestone shows **Pending data**.

---

## Target Types

| Type | Use case |
|---|---|
| Absolute reduction | Commit to reducing total tCO₂e by X% |
| Intensity reduction | Commit to reducing tCO₂e per £revenue (or per unit) by X% |
| Sequestration | Commit to sequestering X tCO₂e through restoration activities |

---

## Reporting Targets

Targets appear in your GHG Protocol PDF report in a dedicated section showing baseline, trajectory, and progress to date. They are also visible in the Dashboard summary.
    `.trim(),
  },

  {
    slug: "reports-exports",
    badge: "Reports",
    time: "4 min read",
    title: "Generating Reports and Exporting Data",
    description:
      "Produce a GHG Protocol PDF report in one click, export raw data to CSV or JSON, and understand what each report field contains.",
    body: `
## Report Types

SusDevOS generates three types of output:

| Report | Format | What it contains |
|---|---|---|
| GHG Inventory Report | PDF | Full GHG Protocol disclosure (see below) |
| Project Carbon Report | PDF | Biomass carbon, sequestration, net balance |
| Data Export | CSV / JSON | Raw emissions records with all fields |

---

## GHG Inventory Report (PDF)

To generate:
1. Navigate to **Emissions → Inventories → [Inventory]**.
2. Click **Generate Report → GHG Protocol PDF**.
3. The report is queued, generated, and available in **Reports → My Reports** within seconds.

The PDF includes:

- **Cover page** — entity name, reporting year, report date
- **Organisational boundary** — consolidation approach, boundary notes
- **Methodology** — emission factor sources (DEFRA, EPA, Climatiq), GWP dataset (IPCC AR6/AR5/AR4)
- **Scope 1 total** with source breakdown
- **Scope 2 totals** — both location-based and market-based
- **Scope 3 totals** by category, with relevance assessment notes
- **Biogenic CO₂** — separate disclosure
- **Carbon offsets** — validated credits and net position
- **Targets and progress** (if targets are set)
- **Data quality assessment**

---

## Project Carbon Report (PDF)

Navigate to **Projects → [Project] → Generate Report → Project Carbon**.

Contains:
- Land parcel map
- Tree removal carbon stock calculations
- Restoration sequestration projections (30-year)
- Net carbon balance (removals minus sequestration)
- Species and ecosystem summary (if biodiversity records exist)

Suitable for planning applications, Environmental Impact Assessments, and green finance documentation.

---

## CSV / JSON Export

Navigate to **Reports → Export Data**.

Select:
- **Entity** (defaults to active entity)
- **Date range**
- **Scope filter** (all, Scope 1 only, etc.)
- **Format** (CSV or JSON)

The export includes all fields: activity quantity, unit, emission factor value and source, GWP value, calculated tCO₂e, scope, category, project link, and verification status.

---

## Downloading Stored Reports

All generated reports are stored and available for re-download at any time from **Reports → My Reports**. Reports are not deleted when inventory data is updated — they represent a point-in-time snapshot.
    `.trim(),
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getGuide(slug: string): Guide | undefined {
  return GUIDES.find((g) => g.slug === slug);
}

// ─────────────────────────────────────────────────────────────────────────────
// Static params (pre-generate all guide paths at build time)
// ─────────────────────────────────────────────────────────────────────────────

export function generateStaticParams() {
  return GUIDES.map((g) => ({ slug: g.slug }));
}

// ─────────────────────────────────────────────────────────────────────────────
// Per-guide SEO metadata
// ─────────────────────────────────────────────────────────────────────────────

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const guide = getGuide(params.slug);
  if (!guide) return { title: "Not found" };
  return {
    title: `${guide.title} — SusDevOS Guides`,
    description: guide.description,
    alternates: {
      canonical: `https://susdevos.com/resources/guides/${guide.slug}`,
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function GuidePage({ params }: { params: { slug: string } }) {
  const guide = getGuide(params.slug);
  if (!guide) notFound();

  return (
    <div
      className="min-h-screen"
      style={{
        background: [
          "radial-gradient(ellipse 60% 40% at 50% 0%, rgba(22,163,74,0.08) 0%, transparent 60%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      <div className="mx-auto max-w-3xl px-4 sm:px-6 py-14">
        {/* Back link */}
        <Link
          href="/resources/guides"
          className="mb-8 inline-flex items-center gap-2 text-sm text-surface-400 hover:text-brand-300 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          All guides
        </Link>

        {/* Header */}
        <header className="mb-10">
          <div className="mb-4 flex items-center gap-3">
            <span className="rounded-full border border-brand-500/20 bg-brand-500/10 px-3 py-0.5 text-xs font-medium text-brand-300">
              {guide.badge}
            </span>
            <span className="flex items-center gap-1.5 text-xs text-surface-500">
              <Clock className="h-3.5 w-3.5" />
              {guide.time}
            </span>
          </div>
          <h1 className="mb-3 text-3xl font-bold text-white sm:text-4xl">
            {guide.title}
          </h1>
          <p className="text-lg text-surface-400">{guide.description}</p>
        </header>

        {/* Divider */}
        <hr className="mb-10 border-surface-700" />

        {/* Body — markdown rendered */}
        <article
          className="prose prose-invert prose-sm sm:prose-base max-w-none
          prose-headings:text-white
          prose-h2:text-xl prose-h2:font-semibold prose-h2:mt-10 prose-h2:mb-4
          prose-h3:text-base prose-h3:font-semibold prose-h3:mt-6 prose-h3:mb-2
          prose-p:text-surface-300 prose-p:leading-relaxed
          prose-a:text-brand-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-white
          prose-code:text-brand-300 prose-code:bg-surface-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
          prose-pre:bg-surface-800 prose-pre:border prose-pre:border-surface-700
          prose-blockquote:border-l-brand-500 prose-blockquote:text-surface-400
          prose-table:text-sm
          prose-thead:border-surface-700
          prose-th:text-surface-300 prose-th:font-semibold
          prose-td:text-surface-400 prose-td:border-surface-700/50
          prose-tr:border-surface-700/50
          prose-li:text-surface-300
          prose-hr:border-surface-700"
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {guide.body}
          </ReactMarkdown>
        </article>

        {/* Bottom nav */}
        <div className="mt-14 pt-8 border-t border-surface-700 flex items-center justify-between">
          <Link
            href="/resources/guides"
            className="inline-flex items-center gap-2 text-sm text-surface-400 hover:text-brand-300 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            All guides
          </Link>
          <Link
            href="/contact"
            className="text-sm text-surface-400 hover:text-brand-300 transition-colors"
          >
            Questions? Contact support →
          </Link>
        </div>
      </div>
    </div>
  );
}

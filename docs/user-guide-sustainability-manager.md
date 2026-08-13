# SusDevOS Guide for Sustainability Managers — GHG Inventories, Scope 3, Reduction Targets & Reporting

**Who this guide is for:** Sustainability managers and ESG leads responsible for producing an organisation's annual GHG inventory. You may hold the Admin or Manager role. This guide follows the GHG Protocol Corporate Standard and explains how SusDevOS implements each step.

**What you can do:**
- Record Scope 1, 2, and 3 emissions using DEFRA, EPA, or Climatiq emission factors
- Build and submit a formal GHG inventory
- Set reduction targets and track milestone progress
- Manage carbon offsets and validate them against Verra and Gold Standard registries
- Generate PDF, CSV, and JSON reports

---

## 1. How GHG Calculations Work in SusDevOS

Understanding this saves troubleshooting time later.

**The calculation is always server-side.** When you save an emissions record, SusDevOS computes:

```
Emissions (kg CO₂e) = Quantity × Emission Factor × GWP₁₀₀
```

You never enter a CO₂e figure directly — it is always calculated. If you paste in a tCO₂e from a supplier invoice, it will be overwritten. Enter the raw quantity (kWh, litres, tonnes of material, £ spend) and let SusDevOS calculate.

**Scope 2 always produces two numbers.** The GHG Protocol requires both the location-based and market-based Scope 2 figures. SusDevOS calculates both every time you save a Scope 2 record. You need to supply:
- A grid emission factor (for location-based) — defaults to national average if not set
- An energy attribute certificate (EAC) emission factor (for market-based) — 0 if you hold REGOs/GOs/RECs

**Biogenic CO₂ is separate.** If your Scope 1 includes biomass combustion (wood pellets, biogas), the biogenic CO₂ is calculated and stored separately in `BiogenicCO2AmountTonnes`. It does not appear in your GWP total — this is correct GHG Protocol behaviour (LULUCF accounting). It is reported in a separate column in your inventory report.

**GWP dataset.** SusDevOS defaults to IPCC AR6 GWP100 (2021). You can switch to AR5 or AR4 in **Settings → Calculation Settings** if required by your reporting standard. The change affects all new calculations; existing records retain their GWP value until you trigger a recalculation.

---

## 2. Building Your Annual GHG Inventory

The workflow is: create an inventory → add emissions records → review totals → submit for verification → generate report.

### 2.1 Create a GHG inventory

1. Navigate to **Emissions → Inventories → New Inventory**.
2. Fill in:
   - **Reporting Year** — the calendar or fiscal year you are reporting (e.g. 2024).
   - **Base Year** — the baseline year your reduction targets are measured against. Usually the first year you have complete data.
   - **Consolidation Approach** — must match your Entity setting (Equity Share, Financial Control, or Operational Control).
   - **Boundary Notes** — describe what is included and excluded (e.g. "Includes UK operations only; excludes leased vehicles below 3.5t GVW").
3. Click **Create**. The inventory is created with `VerificationStatus = 0` (Draft).

### 2.2 Record Scope 1 emissions (direct)

Scope 1 covers direct combustion, process emissions, and fugitive emissions from assets your organisation owns or controls.

**Common Scope 1 categories:**
- Natural gas combustion (boilers, furnaces) — enter kWh or cubic metres
- Company vehicle fuel (petrol, diesel) — enter litres
- Refrigerant top-ups (HFCs) — enter kg of refrigerant
- Biomass combustion — enter tonnes of fuel (biogenic CO₂ handled automatically)

1. Navigate to **Emissions → Records → New Record**.
2. Set **Scope = 1**.
3. Select the **Emission Factor Set** (DEFRA is the default for UK operations).
4. Select the specific **Emission Factor** (e.g. "Natural Gas — kWh (net CV)").
5. Enter the **Quantity** and **Unit**.
6. Optionally link to a **Project** or **Land Parcel** for project-level reporting.
7. Click **Save**. The tCO₂e appears immediately.

### 2.3 Record Scope 2 emissions (purchased electricity, heat, steam)

1. Create a new record with **Scope = 2**.
2. Select your electricity grid and enter kWh consumed.
3. If you hold energy attribute certificates (REGOs, GOs, RECs): enter `0` as the market-based emission factor, or select your supplier's certified zero-carbon tariff from the EF library.
4. Both `EmissionsAmountLocationBased` and `EmissionsAmountMarketBased` are calculated and stored.

**For GHG Protocol dual reporting:** your inventory report shows both figures. Under the GHG Protocol Scope 2 Guidance, market-based is typically presented as the primary figure, with location-based disclosed separately.

### 2.4 Record Scope 3 emissions (value chain)

Scope 3 covers 15 categories. Common ones for property and infrastructure companies:

| Category | What to measure | Typical input |
|----------|----------------|--------------|
| Cat 1: Purchased goods & services | Embodied carbon in materials | Spend (£) × spend-based EF, or mass × material EF |
| Cat 3: Fuel & energy (T&D losses) | Grid losses for purchased electricity | Calculated automatically from Scope 2 inputs |
| Cat 5: Waste generated in operations | Skip hire, office waste | Tonnes by waste type |
| Cat 6: Business travel | Flights, rail, hotels | Passenger-km or nights |
| Cat 11: Use of sold products | Embodied carbon in buildings sold | m² floor area × EF |
| Cat 15: Investments | Financed emissions | Portfolio method or PCAF approach |

1. Create a new record with **Scope = 3** and select the **Category** (1–15).
2. Select the appropriate emission factor.
3. Enter quantity.

> **Free plan:** Scope 3 is not available. You can record Scope 1 and 2 only. Upgrade to Starter to unlock all 15 categories.

### 2.5 Review your inventory totals

Navigate to **Emissions → Inventories → [your inventory]**.

The summary panel shows:
- **Gross Scope 1 / Scope 2 (location) / Scope 2 (market) / Scope 3** tCO₂e
- **Carbon offsets** (if any)
- **Net emissions** (gross minus verified offsets)
- **Biogenic CO₂** — shown separately, not included in net

Totals update in real time as you add records. If a total shows as blank, it means a background recalculation task hasn't run yet — refresh in a minute.

---

## 3. Managing Carbon Offsets

Carbon offsets reduce your net emissions figure. SusDevOS validates offsets against the Verra VCS and Gold Standard registries.

1. Navigate to **Emissions → Offsets → New Offset**.
2. Enter the **Registry** (Verra or Gold Standard), **Project ID**, **Vintage Year**, and **Quantity** (tCO₂e).
3. Click **Save**. SusDevOS queues a background validation against the registry.
4. Within 24 hours, the offset status updates:
   - **Validated** — project exists and credits are live in the registry.
   - **Retired** — credits have been retired, suitable for reporting.
   - **Pending** — registry could not be reached; will retry.
   - **Invalid** — project ID not found; do not include in reporting.

Only offsets with status **Retired** or **Validated** are subtracted from your gross emissions in the net figure.

---

## 4. Setting and Tracking Reduction Targets

SusDevOS provides generic reduction targets and milestones. You define the base year, target year, and reduction percentage yourself — SusDevOS does not validate targets against, or sync with, any external target registry.

### 4.1 Create a target

1. Navigate to **Emissions → Targets → New Target**.
2. Fill in:
   - **Target type** — Near-term (5–10 year), Long-term (e.g. net-zero by 2050), or both.
   - **Base year** — must match your GHG inventory.
   - **Target year** — e.g. 2030 (near-term) and 2050 (long-term).
   - **Reduction percentage** — e.g. 50% absolute reduction by 2030.
   - **Scope coverage** — which scopes the target covers.
3. Click **Save**.

### 4.2 Track milestone progress

SusDevOS creates annual milestones (linear interpolation from base year to target year).

1. Navigate to **Emissions → Targets → [your target] → Milestones**.
2. Each milestone shows:
   - **Target tCO₂e** — the reduction pathway point for that year.
   - **Actual tCO₂e** — populated automatically from verified inventories.
   - **On track** — green if actual ≤ target; red if exceeded.

Milestones link to inventories automatically once an inventory for that year is verified. The Celery task `link_milestone_actuals` runs nightly.

---

## 5. Generating Reports

### 5.1 Standard PDF report

1. Navigate to **Reports → New Report**.
2. Select:
   - **Report type** — Entity GHG Inventory, Project Emissions Summary, Phase Progress vs Goals, or Tree Removal & Restoration Log.
   - **Inventory** — the reporting year to include.
   - **Format** — PDF.
3. Click **Queue Report**. Report generation runs as a background task (typically 30–90 seconds).
4. When the status shows **Complete**, click **Download** for a pre-signed S3 link (valid 1 hour).

> **Plan notes:**
> - Free: PDF with SusDevOS watermark.
> - Starter / Professional: unbranded PDF.
> - Agency: white-label PDF with your logo.

### 5.2 CSV / JSON export

Available on Starter and above. Export from **Emissions → Records → Export**. Includes all emission records for the selected inventory with raw quantities, factors, and calculated amounts.

---

## 6. Key Calculations Reference

| Concept | How SusDevOS handles it |
|---------|------------------------|
| GWP | IPCC AR6 GWP100 by default. Configurable per inventory. |
| Scope 2 dual method | Both methods always calculated. Market-based used in net total by default. |
| Biogenic CO₂ | Stored separately; excluded from GWP total. |
| Unit conversion | Performed server-side before applying EF. All results in tCO₂e. |
| Net emissions | Gross Scope 1+2+3 minus verified offsets. |
| Verification immutability | VerificationStatus ≥ 3 → no changes permitted. |

---

## 7. Common Questions

**Q: I changed an emission factor — why haven't my totals changed?**
A: Old records retain the EF that was active when they were saved. To recalculate with the new EF, edit each record and re-save, or contact your Admin to run a bulk recalculation.

**Q: My Scope 2 location-based and market-based figures are the same.**
A: You haven't supplied an EAC emission factor. Edit the record and set the market-based EF to `0` if you hold renewable energy certificates, or to your supplier's certified EF.

**Q: The biogenic CO₂ column in my report is non-zero. Is this a mistake?**
A: No. If you burn biomass (wood, biogas), the biogenic CO₂ is calculated and disclosed separately. It is not included in your GWP total per GHG Protocol guidance. Regulators and frameworks like SECR expect this column.

**Q: Can I import emissions data from a spreadsheet?**
A: Yes, on Professional plan and above. Navigate to **Emissions → Import** and upload a CSV using the provided template. The template maps to the same fields as the manual entry form.

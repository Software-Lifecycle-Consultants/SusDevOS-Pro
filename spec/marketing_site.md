# Marketing Site Specification — SusDevOS

> ⚠️ **Scope note (nature/MRV + TNFD refocus).** SBTi and CDP are **out of product
> scope** (see CLAUDE.md § Product scope). The dedicated SBTi feature page, the
> `/standards` SBTi & CDP entries, and the SBTi integration have been removed, and all
> positioning copy (homepage hero, SEO, trust-bar badges, guides, blog calendar) has
> been reframed around the GHG Protocol, IPCC, TNFD, and carbon-credit MRV
> (Verra/Gold Standard). Do not reintroduce SBTi/CDP as product capabilities.

The marketing site is a separate Next.js app (or static site via Astro/Hugo) deployed at the root domain. The Django app serves `/app/*`. All marketing pages are publicly accessible, fully SEO-indexed, and link to `/app/register` for signup CTAs.

---

## Site Structure

```
/ (homepage)
/features
/features/ghg-reporting
/features/ecosystem-tracking
/features/team-and-verification
/pricing
/standards
/integrations
/resources
/resources/guides
/resources/tools/carbon-estimator
/blog
/blog/{slug}
/security
/about
/contact
/demo
/changelog
/legal/privacy
/legal/terms
/legal/dpa          (Data Processing Agreement — needed for enterprise)
```

---

## 1. Homepage `/`

**SEO**
- Title: `SusDevOS — GHG Reporting & Ecosystem Tracking for Development Projects`
- Description: `Calculate your Scope 1, 2 and 3 emissions, track biodiversity and ecosystem impacts, and generate GHG Protocol-conformant reports. Free to start. Built on GHG Protocol, IPCC and TNFD.`
- Keywords: `GHG reporting software, carbon footprint calculator, Scope 3 emissions, TNFD biodiversity reporting, IPCC biomass carbon, carbon credit MRV, emissions inventory`
- OG image: Dashboard screenshot showing a completed GHG inventory summary

**Section 1 — Hero**

Headline (H1): `Your GHG inventory, verified and submission-ready — without the spreadsheet hell.`

Sub-headline: `SusDevOS calculates Scope 1, 2 and 3 emissions, tracks ecosystem and biodiversity impacts, and generates audit-ready reports aligned to the GHG Protocol, IPCC and TNFD. Free to start.`

Two CTAs side by side:
- Primary: `Start for free` → `/app/register`
- Secondary: `Book a demo` → `/demo`

Visual: Animated mockup cycling between (a) the emissions data entry form with auto-populated emission factors, (b) the GHG inventory dashboard showing Scope 1/2/3 totals, (c) a generated PDF report cover page.

**Section 2 — Trust bar**

Text: `Aligned to the standards that matter`
Logos/badges (inline, greyscale): GHG Protocol Corporate Standard, IPCC, TNFD, Verra, Gold Standard, UN-SDGs
Copy underneath each: short one-liner explaining the alignment (e.g. "GHG Protocol — all 15 Scope 3 categories supported")

**Section 3 — Problem statement**

Headline: `Most sustainability teams are still working in Excel. That's a problem.`

Three pain points in a three-column grid:
1. **"Our data is all over the place"** — Activity data in one spreadsheet, emission factors in another, reports emailed as PDFs. One wrong formula breaks the whole inventory.
2. **"We can't prove our numbers"** — Auditors and verifiers need a full calculation trail. Spreadsheets don't provide one.
3. **"It takes months every year"** — Manual data collection, chasing suppliers for Scope 3 data, formatting reports. The same work, repeated annually.

Below the grid: `SusDevOS solves all three.`

**Section 4 — How it works**

Headline: `From activity data to verified report in three steps`

Step 1 — `Enter your activity data`
Copy: Enter fuel consumption, electricity use, business travel, purchased goods — in the units you already have. Emission factors from DEFRA, EPA and the IPCC are applied automatically.

Step 2 — `Review your calculated inventory`
Copy: See your Scope 1, 2 and 3 totals in real time. Track progress against your emissions reduction targets. Flag data quality issues before they become audit findings.

Step 3 — `Generate and submit your report`
Copy: One click produces a GHG Protocol-conformant PDF, ready for verifier review, assurance, or internal disclosure. Full calculation methodology included.

**Section 5 — Feature highlights (persona tabs)**

Tab labels: `For sustainability managers` / `For ESG consultants` / `For development projects`

**Sustainability managers tab:**
- Auto-populated emission factors (DEFRA 2024, EPA eGRID, Climatiq)
- Scope 3 relevance assessment — guided checklist for all 15 categories
- Emissions reduction targets with milestone progress tracking
- Verification workflow — internal review → third-party sign-off
- Audit-ready PDF & CSV export

**ESG consultants tab:**
- Manage up to 25 client entities from one login
- White-label PDF reports with your branding
- Client read-only portal — share results without sharing the login
- Bulk data import for multi-client annual reporting

**Development projects tab:**
- Land parcel and ecosystem mapping (PostGIS-powered)
- Tree removal carbon stock calculations (IPCC Tier 1/2/3)
- Restoration sequestration tracking
- TNFD-aligned biodiversity impact reporting
- Planning consent and green finance documentation support

**Section 6 — Social proof**

If no customers yet: replace with a "what our beta testers say" block with quotes from pilot users, or a "Built on trusted data" block highlighting DEFRA, IPCC, Climatiq, Verra data sources.

Once customers exist: 3 case study cards (company logo, sector, one-line result e.g. "Reduced Scope 3 reporting time from 3 months to 2 weeks").

**Section 7 — Pricing teaser**

Headline: `Start free. Scale as you grow.`

Three-column preview of Free / Starter / Professional with key limits and price. Link to full pricing page.

Free CTA: `Start for free — no credit card required`

**Section 8 — Embedded carbon estimator**

Headline: `How big is your carbon footprint? Find out in 60 seconds.`

Three-question inline form:
1. Industry sector (dropdown — maps to Scope 3 category weights)
2. Number of employees (ranges: 1–10, 11–50, 51–200, 201–500, 500+)
3. Country (ISO2 dropdown — determines grid EF for Scope 2 estimate)

Output: Estimated total tCO2e range (Scope 1+2, indicative) + "Get your precise inventory in SusDevOS" CTA.

Email gate: show rough estimate inline, offer to email a detailed breakdown (captures lead, triggers welcome drip).

**Section 9 — Footer**

Columns: Product (Features, Pricing, Integrations, Changelog) / Resources (Blog, Guides, API Docs, Standards) / Company (About, Contact, Careers) / Legal (Privacy, Terms, DPA, Security)

Social: LinkedIn, GitHub (if open-sourcing any components), Twitter/X

Bottom bar: `© 2025 SusDevOS. GHG Protocol, TNFD, IPCC, Verra and Gold Standard are trademarks of their respective owners.`

---

## 2. Features `/features`

**SEO**
- Title: `Features — GHG Reporting, Ecosystem Tracking & TNFD Nature Reporting | SusDevOS`
- Description: `Explore SusDevOS features: automated emission factor lookup, Scope 1/2/3 calculation, IPCC biomass carbon, carbon-credit MRV, verification workflow and TNFD-aligned reporting.`

**Structure:**

Hero: `Everything you need for credible climate disclosure` + link to all four feature detail pages.

Three feature cards linking to sub-pages:
1. GHG Reporting — DEFRA/EPA EFs, Scope 2 dual method, Scope 3 categories
2. Ecosystem Tracking — land parcels, tree removals, IPCC biomass, restorations, TNFD
3. Team & Verification — roles, approval workflow, third-party verification

---

## 3. Feature Detail Pages

### `/features/ghg-reporting`

**SEO**
- Title: `GHG Reporting Software — Scope 1, 2 and 3 Calculations | SusDevOS`
- Description: `Calculate Scope 1, 2 and 3 greenhouse gas emissions with auto-populated DEFRA and EPA emission factors. GHG Protocol-conformant inventory generation in minutes.`
- Keywords: `Scope 3 software, GHG inventory tool, emission factor database, carbon accounting software UK`

**Sections:**
1. Hero: "Calculate every scope. Miss nothing."
2. Scope 1 — stationary combustion, mobile, fugitives. Show fuel → tCO2e calculation inline.
3. Scope 2 — dual method (location-based + market-based). Explain why both matter under the GHG Protocol Scope 2 Guidance.
4. Scope 3 — all 15 categories. Interactive checklist showing relevance assessment flow.
5. Emission factor library — DEFRA 2024, EPA eGRID, Climatiq, IPCC. Auto-updates annually.
6. Biogenic CO2 — explain why it's reported separately and where it appears in the report.
7. Report output — PDF mockup with GHG Protocol-required disclosure elements labelled.

### `/features/ecosystem-tracking`

**SEO**
- Title: `Ecosystem & Biodiversity Tracking for Development Projects | SusDevOS`
- Description: `Map land parcels, calculate IPCC Tier 1-3 biomass carbon from tree removals, track restoration sequestration, and report biodiversity impacts aligned to TNFD.`
- Keywords: `TNFD reporting tool, biodiversity impact assessment, IPCC biomass carbon calculation, restoration carbon tracking`

**Sections:**
1. Hero: "Go beyond carbon. Track your impact on nature."
2. Land parcel mapping — PostGIS map showing parcels with ecosystem overlays
3. Tree removal carbon — IPCC Tier 1/2/3 BEF method, formula shown visually
4. Restoration sequestration — annual rate × area × years, permanence risk disclosure
5. TNFD alignment — map to TNFD LEAP framework (Locate, Evaluate, Assess, Prepare)
6. Species tracking — GBIF/IUCN integration, conservation status disclosure

### ~~`/features/sbti-progress`~~ — REMOVED (out of scope)

> SBTi is out of product scope (nature/MRV + TNFD refocus — see CLAUDE.md § Product
> scope). This dedicated page is removed. Generic emissions targets and milestone
> tracking (the `Targets` model) remain and can be surfaced within the GHG Reporting
> page if needed — but not framed as an SBTi feature.

### `/features/team-and-verification`

**SEO**
- Title: `Team Collaboration & GHG Inventory Verification | SusDevOS`
- Description: `Role-based access control, internal approval workflows, and third-party verification support for ISO 14064-3 and ISAE 3410 assurance. Audit trail for every change.`

**Sections:**
1. Hero: "From data entry to verified inventory — all in one place."
2. Roles — table showing what each role can do (DataEntry, Reviewer, Approver, Admin, SuperAdmin)
3. Approval workflow — diagram: Draft → Submitted → Reviewed → Approved → Verified
4. Verification support — assurance levels (Limited/Reasonable), verifier organisation field, immutable verified records
5. Audit log — every change, who made it, timestamp, old and new values. Retained per regulatory tier.

---

## 4. Pricing `/pricing`

**SEO**
- Title: `Pricing — Free GHG Reporting to Enterprise | SusDevOS`
- Description: `SusDevOS is free for one entity. Starter from £49/month. Agency plans for sustainability consultants. Transparent pricing with no hidden fees.`

**Structure:**
- Monthly/Annual toggle (annual shows 20% saving)
- Five-column comparison table (see spec/pricing.md for full matrix)
- Entity add-on callout: "Need more entities? Add them at £15/month each."
- FAQ section (see below)
- Enterprise CTA: "More than 25 entities or need a dedicated instance? Let's talk."

**Pricing FAQ:**
- "What counts as an entity?" — A legal entity: a company, subsidiary, or branch with its own GHG inventory boundary.
- "Can I switch plans?" — Yes, upgrades take effect immediately. Downgrades take effect at next billing date.
- "Is there a free trial for paid plans?" — 14-day trial on Starter and Professional, no credit card required.
- "Do you offer discounts for NGOs or academia?" — Yes. Contact us for a 50% non-profit discount.
- "What happens to my data if I downgrade?" — Data is retained for 90 days. You can export at any time.
- "Is VAT included?" — Prices shown ex-VAT. UK VAT (20%) added at checkout for UK customers.

---

## 5. Standards & Compliance `/standards`

**SEO**
- Title: `GHG Protocol, IPCC, TNFD & SDG Compliance | SusDevOS`
- Description: `SusDevOS is built on the GHG Protocol Corporate Standard, IPCC 2006 Guidelines, and the TNFD framework. Understand how each standard is implemented.`

**Sections — one per standard:**

**GHG Protocol Corporate Standard**
What it requires → how SusDevOS implements it (Scope 1/2/3, consolidation approaches, biogenic CO2, Scope 2 dual method, Scope 3 relevance assessment). Link to ghg_calculation_spec.md (public version).

**TNFD (Taskforce on Nature-related Financial Disclosures)**
LEAP framework (Locate, Evaluate, Assess, Prepare). How land parcel + ecosystem module maps to TNFD disclosure requirements. Status: aligned, not formally reviewed.

**IPCC Guidelines (2006, LULUCF)**
Tier 1/2/3 biomass carbon methodology. Link to biomass calculation spec. Default parameters sourced from IPCC Tables 4.4, 4.5, 4.13.

**UN Sustainable Development Goals**
SDG mapping: SDG 13 (Climate Action), SDG 15 (Life on Land), SDG 7 (Clean Energy), SDG 11 (Sustainable Cities). How SusDevOS data supports SDG progress reporting.

---

## 6. Integrations `/integrations`

**SEO**
- Title: `Integrations — DEFRA, EPA, Climatiq, Companies House & More | SusDevOS`
- Description: `SusDevOS connects to DEFRA, EPA eGRID, Climatiq, Companies House, Verra, Gold Standard, GBIF and the ECB for automatic emission factors, company data, offset validation and FX rates.`

**Layout:** Logo grid with category headers.

**Emission factor databases**
DEFRA, EPA eGRID, IEA, Climatiq, IPCC 2006 — each with: what data is pulled, cadence, and what it auto-populates in the product.

**Company registries**
Companies House (UK), OpenCorporates (global) — entity auto-population on signup/creation.

**Carbon registries**
Verra (VCS), Gold Standard — offset serial number validation, retirement confirmation.

**Financial data**
ECB, Open Exchange Rates — daily FX rates for spend-based Scope 3.

**Biodiversity**
GBIF, IUCN Red List — species scientific name, taxonomy, conservation status.

**"Want an integration we don't have?"** — link to contact form with "Integration request" subject pre-filled.

---

## 7. Resources `/resources`

**SEO**
- Title: `Sustainability Reporting Resources, Guides & Tools | SusDevOS`
- Description: `Free guides, checklists and tools for GHG reporting, Scope 3 assessment, IPCC biomass carbon and TNFD disclosure. No login required.`

**Sub-pages:**

### Guides (gated by email)
- "Your first GHG inventory: a step-by-step guide" (PDF, ~20 pages)
- "GHG Protocol Scope 3: assessing relevance across all 15 categories" (PDF)
- "How to set and track a credible emissions reduction target" (PDF)
- "TNFD for development projects: a practical introduction" (PDF)
- "Carbon credit MRV: validating Verra & Gold Standard retirements" (PDF)

### Tools (no gate)
- **Carbon estimator** (`/resources/tools/carbon-estimator`) — same tool as homepage section, standalone page for SEO
- **Scope 3 relevance checker** — interactive checklist of the 15 categories with the 5 GHG Protocol relevance criteria as checkboxes. Exports a filled-in relevance assessment table as PDF.
- **GWP converter** — enter kg of a greenhouse gas, select GWP dataset, get tCO2e. Simple, fast, useful to sustainability managers who come to the page from Google.

### Changelog `/changelog`
Public changelog of new features. Builds trust and gives existing users visibility. Format: date, version, what changed (user-facing language, not commit messages). RSS feed available.

---

## 8. Blog `/blog`

**SEO**
- Title: `Sustainability & GHG Reporting Blog | SusDevOS`
- Description: `Practical guides on carbon accounting, Scope 3 reporting, IPCC biomass carbon, TNFD, biodiversity impact and sustainable development — written for sustainability managers.`

**Categories:**
- GHG Reporting (calculation methodology, emission factors, standards)
- Scope 3 (category-by-category guides, supplier engagement)
- Nature & Biodiversity (TNFD, ecosystem, land use)
- Targets & MRV (emissions targets, carbon-credit validation)
- Regulation & Policy (CSRD, SEC climate rules, UK TCFD mandate)
- Product Updates (when significant features ship)

**Priority posts (publish first):**

| Title | Target keyword | Category | Intent |
|-------|---------------|----------|--------|
| How to calculate Scope 2 emissions: location-based vs market-based | "scope 2 emissions calculation" | GHG Reporting | Informational |
| DEFRA 2024 emission factors: what's changed and how to apply them | "DEFRA 2024 emission factors" | GHG Reporting | Informational |
| GHG Protocol Scope 3: which of the 15 categories apply to your business? | "scope 3 categories" | Scope 3 | Informational |
| How to set a credible corporate emissions reduction target | "emissions reduction target" | Targets & MRV | Informational |
| How to calculate IPCC Tier 1 biomass carbon from tree removals | "IPCC biomass carbon calculation" | Nature & Biodiversity | Informational |
| TNFD vs TCFD: the key differences and which you need | "TNFD vs TCFD" | Nature & Biodiversity | Informational |
| UK electricity emission factor 2024: grid average and market-based options | "UK electricity emission factor 2024" | GHG Reporting | Informational |
| Preparing for TNFD nature-related disclosure: a first-timer's guide | "TNFD disclosure" | Nature & Biodiversity | Informational |
| What counts as biogenic CO2 and why does it matter? | "biogenic CO2 reporting" | GHG Reporting | Informational |
| Scope 3 Category 1: calculating purchased goods & services emissions | "scope 3 category 1 purchased goods" | Scope 3 | Informational |

**Post template structure:**
- H1 (exact keyword match)
- 80-word intro (what this post answers, who it's for)
- Table of contents (anchor links)
- Body: 1,200–2,000 words, practical and specific
- At least one worked calculation example with real numbers
- "How SusDevOS handles this" callout box (soft product mention)
- Related posts (3 internal links)
- CTA at end: "Try this in SusDevOS — free for one entity"

---

## 9. Security `/security`

**SEO**
- Title: `Security & Data Privacy | SusDevOS`
- Description: `How SusDevOS protects your emissions data: encryption at rest and in transit, GDPR compliance, role-based access control, audit logs and data residency.`

**Sections:**

**Encryption**
- At rest: AES-256 (PostgreSQL on encrypted volume, S3 server-side encryption)
- In transit: TLS 1.3 minimum. All HTTP redirected to HTTPS.
- Passwords: Argon2id (Django default since 4.0)

**Authentication**
- JWT with 15-minute access tokens + 7-day HttpOnly refresh cookies
- Server-side token revocation (no need to wait for expiry on logout/password change)
- Role-based access control with per-interface privilege granularity

**Data isolation**
- Single-database multi-tenancy with row-level entity scoping via `TenantQueryMiddleware`
- All queries filtered by `EntityId` — no cross-tenant data leakage

**Compliance**
- GDPR — EU data subject rights, DPA available on request, data processor agreements for enterprise
- Data residency — EU-hosted by default (London region). Dedicated instance available for enterprise customers requiring data to stay within a specific jurisdiction.
- Retention — audit logs retained per `RetentionTier` (30 days / 1 year / 7 years per record type)

**Vulnerability disclosure**
Responsible disclosure email: security@susdевos.com (or chosen domain). 90-day coordinated disclosure policy.

**Roadmap** (shows seriousness to enterprise buyers)
- SOC 2 Type II — in progress (target: Q3 2026)
- ISO 27001 — planned 2027
- Pen test — annual, last conducted: [date]

---

## 10. About `/about`

**SEO**
- Title: `About SusDevOS — Our Mission and Team`
- Description: `SusDevOS is built to make credible climate and nature disclosure accessible to every organisation, not just those who can afford big consultancies.`

**Sections:**
- Mission statement (2–3 sentences, not buzzwords)
- Why we built this (founder story — what problem they personally hit)
- Team (photos, names, one-line bio)
- Values (3–4, specific: "We cite our sources", "We don't hide fees", "We build for the sustainability manager, not the consultant")
- Open positions (link to Careers page or "We're hiring" if applicable)
- Press/media mentions (logos + links once coverage exists)

---

## 11. Contact & Demo

### `/contact`

Simple form: Name, Email, Company, Message, Subject (dropdown: General, Sales, Partnership, Press, Integration request, Bug report).

Dedicated email aliases routed to the right team: hello@, sales@, press@, security@.

### `/demo`

Calendly embed (or equivalent) for 30-minute demo booking. Pre-fill questions: Company name, Number of employees, Primary use case (dropdown), Which scopes do you currently report (checkboxes).

Confirmation page: "We'll see you then. In the meantime, [start your free account] or [read the GHG Protocol guide]."

---

## 12. Legal Pages

### `/legal/privacy`
Standard GDPR privacy policy. Data controller details, what data is collected, retention periods, subject access request process, third-party processors list (AWS/DigitalOcean, Stripe, Sentry, Climatiq, etc.).

### `/legal/terms`
Acceptable use, subscription terms, payment terms, SLA (for paid plans), liability limitations, IP ownership (customer owns their data).

### `/legal/dpa`
Data Processing Agreement for enterprise customers. GDPR Article 28 requirements. Available to download as PDF and to sign via DocuSign for enterprise contracts.

---

## Technical Notes

**Stack recommendation for marketing site:** Astro (static output with JS islands) or Next.js App Router. Deploy to Cloudflare Pages or Vercel. Separate from the Django app — no shared session, links to `/app/*` for the product.

**SEO requirements:**
- Sitemap at `/sitemap.xml` — auto-generated, submitted to Google Search Console
- `robots.txt` — allow all marketing pages, disallow `/app/*`
- Open Graph tags on every page (og:title, og:description, og:image)
- Twitter Card meta tags
- Canonical URLs — especially for blog posts syndicated elsewhere
- Schema.org structured data: `Organization`, `SoftwareApplication`, `Article` (on blog posts), `FAQPage` (on pricing page FAQ)
- Core Web Vitals: LCP < 2.5s, CLS < 0.1, FID < 100ms. The carbon estimator JS should be lazy-loaded.

**Analytics:** Plausible (privacy-first, no cookie banner required in UK/EU for basic analytics) or PostHog (if you want product analytics too). Google Analytics only if required — adds cookie consent complexity.

**Lead capture:** ConvertKit or Loops for email sequences triggered by: estimator submission, guide download, demo booking, free account signup.

# Partnerships & Credibility Strategy — SusDevOS

> ⚠️ **Scope note.** Following the nature/MRV + TNFD refocus (see CLAUDE.md § Product
> scope), the **CDP Software Partner Program** and **SBTi tools ecosystem listing**
> tracks below are **out of current product scope** — they require CDP-export /
> SBTi-validation features the product no longer builds. They are retained here as
> historical GTM analysis and possible future options, **not** as active plans.
> Prioritise the in-scope rungs: GHG Protocol conformant-tools list, **TNFD Data &
> Tools Landscape**, Cyber Essentials, and carbon-credit-registry (Verra/Gold
> Standard) credibility. Revisit CDP/SBTi only if product scope changes.

Getting mentioned by UNFCCC or adopted by international bodies is a multi-year process, but it follows a clear ladder. Each rung builds the credibility needed for the next. This document lays out that ladder honestly — what's achievable when, what it requires, and what the payoff is.

**The core principle:** international bodies do not endorse commercial software directly. What they do is maintain lists of conformant tools, host partner ecosystems, and feature organisations doing credible work at their events. The goal is to be in those lists and at those events.

---

## Credibility Ladder — Overview

```
Year 1: Foundation
  └── GHG Protocol conformant tools list
  └── CDP Software Partner Program
  └── Cyber Essentials certification
  └── TNFD Data & Tools Landscape

Year 2: Recognition
  └── SBTi tools ecosystem listing
  └── Race to Zero / Breakthroughs partner
  └── UNFCCC CTCN registration
  └── EFRAG / CSRD tools landscape (EU)
  └── COP side event participation

Year 3: Adoption
  └── UNFCCC NAZCA platform listing
  └── UN Global Compact partnership
  └── National government endorsement (UK DESNZ, DEFRA)
  └── Academic / research partnerships
  └── ISO 14064 conformance statement
```

---

## Tier 1 — Do These First (High Impact, Achievable in Year 1)

### 1. GHG Protocol Conformant Tools List

**Organisation:** World Resources Institute (WRI) + WBCSD (World Business Council for Sustainable Development)

**What it is:** WRI maintains a list of software tools that correctly implement the GHG Protocol Corporate Standard. Being listed is the single most important credibility signal for a GHG accounting tool — it is what sustainability managers and their procurement teams check first.

**How to get listed:**
1. Complete the GHG Protocol's self-assessment checklist (available at `ghgprotocol.org/Third-Party-Databases`)
2. The checklist verifies: correct Scope 1/2/3 categorisation, dual Scope 2 method support, consolidation approaches, biogenic CO2 handling, Scope 3 relevance assessment
3. Submit to WRI via their tools submission form with documentation
4. WRI reviews and lists — no fee, no audit, self-certification

**What SusDevOS needs before applying:**
- Scope 2 dual method ✓ (implemented)
- All 15 Scope 3 categories ✓ (implemented)
- Scope 3 relevance assessment ✓ (implemented)
- Consolidation approaches (equity share, financial/operational control) ✓ (implemented)
- Biogenic CO2 reported separately ✓ (implemented)
- Generate a report that includes GHG Protocol-required disclosure elements — this is the one remaining gap

**Timeline:** Apply at launch, once report generation is complete. Listing typically takes 4–8 weeks after submission.

**Impact:** Listed on `ghgprotocol.org`. Referenced in sustainability manager Google searches. Frequently cited in procurement RFPs as a requirement.

---

### 2. CDP Software Partner Program

**Organisation:** CDP (Carbon Disclosure Project)

**What it is:** CDP runs the world's largest corporate environmental disclosure system — over 23,000 companies disclose through CDP annually. CDP maintains a list of "Approved Software Partners" that can generate CDP-compatible data exports. Being listed drives significant inbound sales from companies preparing their annual CDP submission.

**How to get listed:**
1. Register interest via `cdp.net/en/partner-programs`
2. CDP reviews your product against their questionnaire format requirements
3. Technical integration: your report output must map correctly to CDP questionnaire fields (climate change module: C6 for Scope 1/2, C7 for Scope 3, C4 for targets)
4. Once approved, listed in CDP's "Software Solutions" directory with a link to your pricing page

**What SusDevOS needs:**
- CDP export format for GHG data — new report type `CDP_CLIMATE` mapping EmissionsData + GHGInventories to CDP C6/C7/C4 fields
- Scope 3 disclosure format (categories, relevance decisions, calculation method per category)

**CDP questionnaire mapping (key fields):**

| CDP field | SusDevOS source |
|-----------|----------------|
| C6.1 Scope 1 gross emissions | GHGInventories.TotalScope1Tonnes |
| C6.3 Scope 2 location-based | GHGInventories.TotalScope2LocationBasedTonnes |
| C6.3 Scope 2 market-based | GHGInventories.TotalScope2MarketBasedTonnes |
| C6.5 Scope 3 by category | EmissionsData grouped by Scope3Category |
| C7 Emissions breakdown | EmissionsData by facility/entity |
| C4.1 Targets | Targets model |
| C4.2 Target progress | TargetMilestones.AchievementStatus |

**Timeline:** Build CDP export format in parallel with GHG Protocol submission (same codebase). Apply to partner program Month 2–3.

**Impact:** Listed in CDP's partner directory. CDP emails ~23,000 companies annually with their disclosure platform — software partners get visibility in that communication.

---

### 3. TNFD Data & Tools Landscape

**Organisation:** Taskforce on Nature-related Financial Disclosures (TNFD)

**What it is:** TNFD published its final recommendations in September 2023. They maintain a public landscape of data providers and tools that support the TNFD LEAP framework (Locate, Evaluate, Assess, Prepare). SusDevOS's land parcel + ecosystem module maps directly to TNFD LEAP Phase L (Locate — identify nature-related issues in your footprint).

**How to get listed:**
1. Complete TNFD's Data & Tool Provider self-assessment at `tnfd.global/engage/data-providers`
2. Map your tool's capabilities to TNFD LEAP phases
3. TNFD publishes the landscape biannually — no fee, no audit

**TNFD LEAP mapping for SusDevOS:**

| TNFD LEAP phase | SusDevOS capability |
|----------------|-------------------|
| Locate — identify assets in nature-sensitive areas | Land parcel GIS mapping with ecosystem overlays |
| Evaluate — dependencies and impacts | Ecosystem types per parcel, species affected by tree removals |
| Assess — material risks and opportunities | IUCN conservation status, IPCC biomass carbon stock loss |
| Prepare — strategy and targets | Restoration targets, sequestration tracking |

**Timeline:** Apply after land parcel GIS and TNFD reporting modules are complete. Month 4–6.

**Impact:** Rapidly growing framework — ~6,000 companies committed to TNFD disclosure by 2025. TNFD landscape is a standard reference for sustainability managers evaluating tools.

---

### 4. Cyber Essentials Certification (UK Trust Signal)

Covered in `spec/compliance.md`. From a partnerships perspective, Cyber Essentials is required for:
- UK Government Digital Marketplace (G-Cloud) listing — allows selling to UK public sector without individual procurement processes
- Scottish Government and Welsh Government sustainability reporting contracts
- Many UK enterprise procurement policies

**G-Cloud listing:** Register at `cloudstore.crowncommercial.gov.uk`. Requires Cyber Essentials, GDPR compliance documentation, and a service definition document. Once listed, public sector bodies can purchase directly — significant for local authorities, NHS trusts, universities, and government departments with sustainability reporting obligations.

**Timeline:** Cyber Essentials Month 1–2. G-Cloud application Month 3–4.

---

## Tier 2 — Year 2 Targets (Medium Effort, High Payoff)

### 5. SBTi Tools and Resources Ecosystem

**Organisation:** Science Based Targets initiative (SBTi) — a partnership between CDP, UNGC, WRI, and WWF

**What it is:** SBTi maintains a resources page listing tools that help companies set and track science-based targets. Being listed drives inbound from the ~7,000 companies with SBTi commitments, all of whom need software to track progress.

**How to get listed:**
1. Contact SBTi via `sciencebasedtargets.org/contact-us` with subject "Tool/Resource Listing Request"
2. Demonstrate: correct implementation of absolute contraction targets, SDA methodology support, market-based Scope 2 for target tracking, Scope 3 threshold assessment
3. SBTi reviews and adds to their "Tools and Resources" page

**Additional angle:** SBTi's SME programme (`smesclimatecommitment.org`) helps small businesses make net-zero commitments. A free tier integration or partnership with the SME programme would put SusDevOS in front of thousands of SMEs at the moment of commitment. Contact: `SMEClimateHub@wbcsd.org`.

**Timeline:** Apply Month 8–12, once SBTi registry sync and full target tracking is validated.

---

### 6. Race to Zero / Breakthroughs — UNFCCC Campaign Partner

**Organisation:** UNFCCC secretariat + partners

**What it is:** Race to Zero is the UNFCCC's campaign mobilising non-state actors (companies, cities, regions, investors) to commit to net-zero by 2050. The "Breakthroughs" initiative (launched at COP26) focuses on making clean solutions the affordable, accessible default across key sectors by 2030.

SusDevOS can engage as a **campaign supporter** — an organisation that endorses Race to Zero goals and demonstrates alignment through its product and own operations. This is different from a "partner" in the commercial sense — it's a public commitment and listing.

**How to engage:**
1. Register SusDevOS's own entity as a Race to Zero signatory at `racetozero.unfccc.int/join`
2. Requires: a net-zero commitment for SusDevOS's own operations, a credible near-term target (Scope 1+2 by 2030, Scope 3 by 2040), and a first reporting year
3. Once a signatory, listed in the Race to Zero member directory

**What this gives you:** UNFCCC logo usage rights ("We're a Race to Zero member"), listing in the directory, eligibility for COP side event participation.

**Own operations note:** SusDevOS's own GHG footprint is likely small (a software company with remote/hybrid team). Set up your own entity in SusDevOS, calculate your Scope 1+2+3 (cloud hosting is Scope 2, employee commuting is Scope 3 Category 7), and use the platform to report. This is a powerful marketing story: "we use our own tool to manage our footprint."

**Timeline:** Register Month 6 once own-operations inventory is set up. Signatory listing is immediate upon approval (2–4 weeks).

---

### 7. UNFCCC CTCN — Climate Technology Centre & Network

**Organisation:** UNFCCC Technology Mechanism, hosted by UNEP

**What it is:** The Climate Technology Centre & Network (CTCN) is the operational arm of the UNFCCC Technology Mechanism. It maintains a network of climate technology providers who can be deployed to support developing countries' climate goals. Being in the CTCN network means UNFCCC secretariat staff and national focal points in developing countries can find and recommend SusDevOS.

**How to join:**
1. Apply at `ctc-n.org/network/join-network`
2. Fill out the technology profile: what your technology does, which sectors it addresses, which countries you can serve, cost model
3. No fee — CTCN is a public network
4. Review takes 4–8 weeks; if approved, listed in the CTCN network directory

**Technology profile for SusDevOS:**
- Technology type: GHG measurement, reporting and verification (MRV) software
- Sectors: Energy, Transport, Land Use
- Countries: Global (cloud-based)
- SDGs addressed: SDG 13 (Climate Action), SDG 15 (Life on Land)
- Cost model: Freemium SaaS; reduced pricing for developing country users

**Strategic angle:** National governments in developing countries that have NDCs (Nationally Determined Contributions) under the Paris Agreement need MRV software to track progress. Many cannot afford enterprise tools. SusDevOS's free tier and affordable pricing is specifically relevant. CTCN facilitates technology transfer to these countries — being in the network means you get considered when a country's focal point requests an MRV tool.

**Timeline:** Apply Month 8–12. Concurrently explore whether CTCN has any funded deployment opportunities for MRV tools in target countries.

---

### 8. EFRAG / ESRS — European Sustainability Reporting

**Organisation:** European Financial Reporting Advisory Group (EFRAG) — the body that developed the European Sustainability Reporting Standards (ESRS) under CSRD

**What it is:** EFRAG does not maintain a tools list, but they are building out the ESRS digital taxonomy (XBRL) and working with the European Commission on implementation guidance. The relevant entry point is:

- **GRI (Global Reporting Initiative):** EFRAG collaborated with GRI on ESRS/GRI interoperability. GRI maintains a software solutions list. Contact: `software@globalreporting.org`
- **XBRL Europe / EFRAG Digital Reporting:** Implementing ESRS XBRL tagging in report exports would make SusDevOS one of the first tools to support machine-readable CSRD disclosure. Contact EFRAG's Digital Reporting team.

**Action:** Monitor EFRAG's ESRS XBRL taxonomy publication (expected 2025) and implement tagged export for E1 (climate) and E4 (biodiversity) disclosures. This is a significant technical investment but creates a durable moat.

**Timeline:** Monitor in Year 1. Implement XBRL export in Year 2 once taxonomy is stable.

---

### 9. COP Side Event Participation

**What it is:** COP (Conference of the Parties) is the annual UNFCCC climate summit. Alongside the formal negotiations, there are hundreds of side events — panels, workshops, and exhibitions — where businesses, NGOs, and governments present their work. The COP Blue Zone (official UNFCCC) requires accreditation; the Green Zone (national government hosted) is more accessible.

**How to participate:**
- **COP Blue Zone:** Apply for observer organisation status via UNFCCC observer application. Requires demonstrating relevance to climate change mitigation or adaptation. Status: `NGO` or `Business and Industry NGO (BINGO)`. Apply 6 months in advance.
- **COP Green Zone:** Host country government manages access. Typically easier for businesses. Request a speaking slot or exhibition space through the host country's environment ministry.
- **Pavilions:** Many organisations (WRI, ICLEI, CDP, UK Government) host pavilions at COP where they invite partners to present. If listed on GHG Protocol or CDP tools lists, approach these organisations about presenting from their pavilion.

**What to present:** A live demo of SusDevOS calculating a GHG inventory for a developing-country development project, showing IPCC Tier 1 biomass carbon for a tree removal and restoration sequestration. This is visual, specific, and directly relevant to LULUCF discussions that dominate the land-use track at COP.

**COP 30** takes place in Belém, Brazil in November 2025 — the first COP in the Amazon. Land use, deforestation, and biodiversity will dominate the agenda. SusDevOS's ecosystem module is directly relevant. Aim to have a presence.

**Timeline:** Register for UNFCCC observer status Month 6. Apply for COP30 side event Month 9.

---

## Tier 3 — Year 3 and Beyond (Strategic, Longer-Term)

### 10. UNFCCC NAZCA Platform

**What it is:** The Non-State Actor Zone for Climate Action (NAZCA) tracks commitments by companies, cities, investors, and regions. It is managed by the UNFCCC secretariat. SusDevOS itself joining as a signatory is straightforward (part of Race to Zero above). Getting NAZCA to feature SusDevOS as a tool that other NAZCA signatories use requires a different approach.

**How:** Demonstrate that a meaningful number of NAZCA signatories use SusDevOS. UNFCCC communications team periodically publishes stories about "how companies are meeting their NAZCA commitments." With 3–5 customer case studies showing NAZCA signatories using SusDevOS, approach the UNFCCC communications team (`press@unfccc.int`) with a story pitch. This is earned media, not a formal listing.

**Timeline:** Year 3, once customer base includes recognisable NAZCA signatories.

---

### 11. UN Global Compact Partnership

**Organisation:** United Nations Global Compact (UNGC)

**What it is:** The UN Global Compact is the world's largest corporate sustainability initiative, with ~21,000 companies signed up to its 10 principles. UNGC runs a "solutions marketplace" where tools and services relevant to the SDGs can be listed.

**How to list:**
1. SusDevOS must first become a UNGC signatory (`unglobalcompact.org/participation/join`)
2. Submit to the Solutions Marketplace at `unglobalcompact.org/sdgs/resources`
3. Map to relevant SDGs: SDG 13 (Climate Action), SDG 15 (Life on Land), SDG 9 (Industry, Innovation)

**Additional angle:** UNGC's SDG Ambition programme helps companies set science-based SDG targets. Integration with this programme (e.g. a specific report type showing SDG alignment alongside GHG data) would be a differentiator.

**Timeline:** Year 2–3. Signatory status is immediate; marketplace listing takes 4–8 weeks after application.

---

### 12. National Government Endorsement (UK)

**UK DESNZ (Department for Energy Security and Net Zero):**
The UK government publishes guidance on GHG reporting for companies (mandatory for quoted companies under SECR — Streamlined Energy and Carbon Reporting). DESNZ does not currently maintain a tools list, but they publish methodology guidance that references specific tools. Engaging DESNZ policy team with evidence that SusDevOS correctly implements their guidance (DEFRA EFs, GHG Protocol) could lead to a reference in guidance documentation.

**Action:** Contact `ghg.enquiries@energysecurity.gov.uk` to introduce SusDevOS and offer to participate in any future tools consultation. Monitor SECR guidance updates for opportunities to be referenced.

**DEFRA Official Statistics:**
DEFRA publishes the UK's official GHG emission factor tables annually. Being cited as a tool that correctly implements these factors in DEFRA's own guidance would be significant. This requires a direct relationship with the DEFRA GHG team and demonstrated technical accuracy.

**UK Export Finance (UKEF) / British International Investment (BII):**
UK development finance institutions fund projects in developing countries. Many UKEF-financed projects require environmental impact assessments and GHG calculations. If SusDevOS is used on UKEF-financed projects, UKEF may reference it in their environmental reporting guidance. Engage via `ukef.gov.uk/doing-business-with-us`.

---

### 13. Academic and Research Partnerships

Academic credibility creates long-term legitimacy that commercial partnerships cannot.

**Opportunities:**

**University of Oxford — Smith School of Enterprise and the Environment:**
Runs the Oxford Net Zero initiative. Contact researchers working on MRV methodology and offer SusDevOS as a research tool for PhD students studying corporate GHG accounting. In return: academic papers may reference the tool, and Oxford alumni are heavily represented in sustainability roles at large companies.

**London School of Economics — Grantham Research Institute:**
Leading climate policy research institute. Similar approach — offer research access in exchange for potential citation.

**Open data contribution:**
Publish an anonymised, aggregated dataset of Scope 1+2+3 emissions from consenting SusDevOS users by industry sector and country. This would be genuinely useful to researchers, positions SusDevOS as a data contributor to the field, and generates inbound academic citations. Host at `data.susdевos.com/open`.

**IPCC Working Group III:**
IPCC WG III covers mitigation. Researchers contributing to assessment reports may find SusDevOS's implementation of IPCC Tier 1/2/3 methodologies interesting. Engaging with IPCC chapter authors (they are academics, approachable via email) at the boundary of their work and your implementation is a low-cost way to build credibility. A blog post responding to an IPCC finding, reviewed by an IPCC author, carries significant weight.

---

## Messaging Framework for All Partnership Applications

Every application to an international body needs consistent, credible positioning. Use this framework:

**What SusDevOS is:** An open-standards GHG accounting and ecosystem tracking platform built on GHG Protocol, IPCC, SBTi, and TNFD methodologies, designed to make credible climate disclosure accessible to organisations of all sizes.

**What problem it solves:** The gap between international climate standards (which are technically rigorous) and the tools available to organisations that need to implement them (which are either unaffordable enterprise solutions or inadequate spreadsheets). SusDevOS is built for the 99% of organisations that cannot afford Big 4 consultancy-led reporting.

**Evidence of methodological rigour:** Cite specific implementation details — IPCC Tier 1/2/3 biomass calculation using BEF, Root-to-Shoot ratio, and Carbon Fraction (CF=0.47 IPCC default); GHG Protocol Scope 2 dual-method; all 15 Scope 3 categories with relevance assessment; GWP AR6 values. Having the detail shows you have done the work, not just claimed compliance.

**Development focus:** Explicitly designed for development projects (construction, infrastructure, land use) — an underserved segment where biodiversity and carbon intersect, and where TNFD/CSRD disclosure requirements are most acute.

**Accessibility:** Permanent free tier. Affordable pricing (from £49/month). Available to organisations in developing countries. CTCN-listed technology.

---

## Practical First Steps — Prioritised

| Action | Owner | Timeline | Effort | Impact |
|--------|-------|----------|--------|--------|
| GHG Protocol tools list submission | Founder | Month 1–2 | Low | Very high |
| CDP Software Partner application | Founder + Dev | Month 2–3 | Medium | Very high |
| Register SusDevOS's own entity in the platform | Founder | Month 1 | Low | Medium (story) |
| Cyber Essentials certification | Founder | Month 1–2 | Low | High (UK) |
| G-Cloud listing | Founder | Month 3–4 | Medium | High (UK public sector) |
| TNFD data landscape submission | Founder | Month 4–6 | Low | High |
| Race to Zero signatory registration | Founder | Month 6 | Low | Medium |
| CTCN network application | Founder | Month 8–12 | Low | High (developing countries) |
| SBTi tools listing application | Dev + Founder | Month 8–12 | Medium | High |
| UNFCCC observer status application | Founder | Month 6 | Low | Medium |
| COP30 side event / pavilion | Founder | Month 9 | Medium | Very high |
| GRI software solutions listing | Founder | Month 6–9 | Low | Medium (EU) |
| First academic partnership outreach | Founder | Month 6 | Low | Long-term |

---

## What to Avoid

**Paying for "partnerships" that are just directories.** Many organisations sell "strategic partner" listings. Unless the listing is genuinely searched by your target buyers (GHG Protocol, CDP, TNFD, SBTi are all free and are searched), the ROI is poor.

**Overstating compliance.** Do not say "UNFCCC-approved" or "SBTi-certified" — these phrasings don't exist for software tools and will damage credibility with knowledgeable buyers. Say "aligned to", "built on", "implements the methodology of."

**Claiming conformance before you've been listed.** Submit first, get listed, then use the logo. The GHG Protocol, CDP, and TNFD all have trademark policies.

**Skipping the foundation.** It is tempting to go straight for UNFCCC recognition. But UNFCCC contacts will ask if you're on the GHG Protocol tools list. CDP contacts will ask if you're GHG Protocol conformant. Each tier builds on the previous one.

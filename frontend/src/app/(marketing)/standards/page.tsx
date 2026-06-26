import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle2, ExternalLink } from "lucide-react";

export const metadata: Metadata = {
  title: "Standards — SusDevOS",
  description:
    "SusDevOS is built on GHG Protocol, TNFD, IPCC AR6 and UN SDGs. Read how each standard is implemented — not just referenced.",
  alternates: { canonical: "https://susdevos.com/standards" },
};

// ─────────────────────────────────────────────────────────────────────────────
// Data
// ─────────────────────────────────────────────────────────────────────────────

const STANDARDS = [
  {
    id:        "ghg-protocol",
    abbr:      "GHG Protocol",
    full:      "GHG Protocol Corporate Accounting and Reporting Standard",
    publisher: "World Resources Institute & WBCSD",
    url:       "https://ghgprotocol.org/corporate-standard",
    dot:       "bg-blue-600",
    summary:   "The GHG Protocol Corporate Standard is the most widely used framework for measuring and managing greenhouse gas emissions. It defines the three scope categories that underpin all of SusDevOS's calculations.",
    how: [
      "Scope 1 (direct), Scope 2 (purchased electricity) and Scope 3 (value chain) are calculated using the activity-data × emission-factor method defined in the standard",
      "Organisational boundary approach (equity share, financial control, or operational control) is configured per entity and documented in the inventory",
      "The dual reporting method for Scope 2 is fully implemented — location-based and market-based calculated simultaneously",
      "Biogenic CO₂ is excluded from the GWP total and reported separately in BiogenicCO₂AmountTonnes, as required by the standard",
      "Verified GHG inventories are immutable — once verification status ≥ 3 is reached, edits are rejected at the API level",
      "PDF reports include all GHG Protocol-required disclosures: reporting year, boundary, base year, methodology, emission factors, and GWP source",
    ],
    supplementary: ["GHG Protocol Corporate Value Chain (Scope 3) Standard — all 15 categories", "GHG Protocol Scope 2 Guidance"],
  },
  {
    id:        "tnfd",
    abbr:      "TNFD",
    full:      "Taskforce on Nature-related Financial Disclosures",
    publisher: "TNFD",
    url:       "https://tnfd.global",
    dot:       "bg-lime-600",
    summary:   "TNFD provides a framework for organisations to assess, manage and disclose their nature-related risks and opportunities. SusDevOS supports the LEAP framework for development projects with significant land and ecosystem impacts.",
    how: [
      "LEAP (Locate, Evaluate, Assess, Prepare) assessment structure supported through land parcel and ecosystem data models",
      "Species records include GBIF taxonomy and IUCN Red List conservation status for biodiversity impact assessment",
      "Ecosystem types (woodland, grassland, wetland, etc.) are tracked per land parcel and linked to development projects",
      "IPCC Tier 1/2/3 biomass carbon stock calculations support the 'Evaluate' phase — quantifying nature-related impacts",
      "Restoration sequestration projections support the 'Assess' phase — identifying dependency on healthy ecosystems",
      "Project-level biodiversity reports can be generated for TNFD-aligned disclosure in annual reports and green finance documentation",
    ],
    supplementary: ["TNFD Recommendations v1.0", "TNFD LEAP Approach"],
  },
  {
    id:        "ipcc",
    abbr:      "IPCC",
    full:      "IPCC Sixth Assessment Report & 2006 LULUCF Guidelines",
    publisher: "Intergovernmental Panel on Climate Change",
    url:       "https://www.ipcc.ch",
    dot:       "bg-amber-600",
    summary:   "IPCC provides the scientific basis for GHG accounting. SusDevOS uses IPCC AR6 GWP100 values for all calculations and IPCC 2006 LULUCF guidelines for biomass carbon stock estimation in land and ecosystem accounting.",
    how: [
      "GWP100 values from IPCC AR6 (2021): CO₂ = 1, CH₄ = 29.8 (fossil) / 27.9 (biogenic), N₂O = 273",
      "AR4 and AR5 GWP values are also available — switching GWP dataset recalculates the entire inventory",
      "IPCC 2006 Tier 1 biomass tables used for above-ground biomass density by climate domain and forest type",
      "IPCC 2006 root-to-shoot ratios applied for below-ground biomass estimation",
      "IPCC 2006 basic wood density (D) and biomass expansion factors (BEF) used for Tier 2/3 calculations",
      "30-year sequestration projections for restoration activities use IPCC growth curve parameters per ecosystem type",
    ],
    supplementary: [
      "IPCC AR6 WGI Chapter 7 (GWP values)",
      "IPCC 2006 Guidelines Volume 4 — Agriculture, Forestry and Other Land Use",
    ],
  },
  {
    id:        "sdgs",
    abbr:      "UN SDGs",
    full:      "UN Sustainable Development Goals",
    publisher: "United Nations",
    url:       "https://sdgs.un.org",
    dot:       "bg-indigo-600",
    summary:   "SusDevOS maps platform capabilities to relevant SDGs, helping sustainability teams demonstrate contribution to the global agenda in board reports and ESG disclosures.",
    how: [
      "SDG 13 (Climate Action) — GHG inventory and verified emissions reporting directly support corporate climate commitments",
      "SDG 15 (Life on Land) — TNFD LEAP assessments, species tracking, IUCN status, and restoration sequestration address biodiversity and ecosystem health",
      "SDG 7 (Affordable and Clean Energy) — Scope 2 market-based reporting supports renewable energy procurement transparency",
      "SDG 11 (Sustainable Cities) — Land parcel and development project tracking supports sustainable urban development disclosures",
    ],
    supplementary: ["UN SDG Compass (GRI, UNGC, WBCSD)"],
  },
];

// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-28"
      style={{
        background: [
          "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(22,163,74,0.14) 0%, transparent 70%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-brand-400">
          Standards & frameworks
        </p>
        <h1 className="mx-auto mb-5 max-w-3xl text-4xl font-bold text-white sm:text-5xl lg:text-6xl leading-tight">
          Built on the standards.{" "}
          <span
            className="text-transparent"
            style={{
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              backgroundImage: "linear-gradient(135deg, #4ade80 0%, #2dd4bf 100%)",
            }}
          >
            Not just aligned to them.
          </span>
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-lg text-surface-300 leading-relaxed">
          SusDevOS implements the GHG Protocol, TNFD and IPCC at the calculation
          and methodology level — not just in the reporting layer. Here&apos;s exactly how.
        </p>
        {/* Standard pills */}
        <div className="flex flex-wrap justify-center gap-2">
          {STANDARDS.map(({ id, abbr, dot }) => (
            <a
              key={id}
              href={`#${id}`}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-surface-300 transition-colors hover:border-white/20 hover:text-white"
            >
              <span className={`h-2 w-2 rounded-full ${dot}`} />
              {abbr}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function StandardCard({
  id, abbr, full, publisher, url, dot, summary, how, supplementary,
}: typeof STANDARDS[0]) {
  return (
    <section id={id} className="scroll-mt-20 border-b border-surface-100 py-16 sm:py-20 last:border-0">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid gap-10 lg:grid-cols-[2fr_3fr] lg:gap-16">
          {/* Left: identity */}
          <div>
            <div className="mb-4 flex items-center gap-3">
              <span className={`h-3 w-3 rounded-full ${dot} shrink-0`} />
              <span className="text-xs font-bold uppercase tracking-widest text-surface-400">{abbr}</span>
            </div>
            <h2 className="mb-2 text-2xl font-bold text-surface-900 leading-tight">{full}</h2>
            <p className="mb-1 text-sm text-surface-400">Published by {publisher}</p>
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="mb-5 inline-flex items-center gap-1 text-sm text-brand-600 hover:text-brand-700"
            >
              Official documentation <ExternalLink className="h-3 w-3" />
            </a>
            <p className="text-surface-600 leading-relaxed">{summary}</p>

            {supplementary.length > 0 && (
              <div className="mt-5 rounded-xl border border-surface-200 bg-surface-50 p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-surface-400">Also implemented</p>
                <ul className="space-y-1">
                  {supplementary.map((s) => (
                    <li key={s} className="text-sm text-surface-600">{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right: how */}
          <div>
            <p className="mb-5 text-xs font-semibold uppercase tracking-wider text-surface-400">
              How SusDevOS implements this
            </p>
            <ul className="space-y-4">
              {how.map((point) => (
                <li key={point} className="flex items-start gap-3">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
                  <span className="text-sm leading-relaxed text-surface-600">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function Disclaimer() {
  return (
    <section className="bg-surface-50 py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="text-center text-xs text-surface-400 max-w-3xl mx-auto">
          GHG Protocol, TNFD, IPCC and UN SDGs are trademarks or registered marks of their
          respective owners. SusDevOS is not affiliated with, endorsed by, or officially certified
          by any of these organisations. &quot;Aligned to&quot; and &quot;implements&quot; describe SusDevOS&apos;s
          use of these publicly available methodologies and frameworks in its calculation and reporting engine.
        </p>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function CTA() {
  return (
    <section className="relative overflow-hidden bg-brand-600 py-20">
      <div
        className="pointer-events-none absolute inset-0 opacity-10"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <h2 className="mb-4 text-3xl font-black text-white sm:text-4xl">
          Standards-aligned from day one.
        </h2>
        <p className="mx-auto mb-8 max-w-lg text-brand-100">
          Your first GHG inventory, verified and ready for your auditor, Verra/Gold Standard, and your board.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-brand-700 shadow-lg transition-colors hover:bg-brand-50"
          >
            Start for free <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 rounded-xl border border-brand-400/50 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
          >
            Book a demo
          </Link>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

export default function StandardsPage() {
  return (
    <>
      <Hero />
      <div className="bg-white">
        {STANDARDS.map((s) => (
          <StandardCard key={s.id} {...s} />
        ))}
      </div>
      <Disclaimer />
      <CTA />
    </>
  );
}

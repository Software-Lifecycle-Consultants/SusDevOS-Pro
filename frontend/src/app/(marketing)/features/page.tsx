import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight, BarChart3, CheckCircle2, Shield, FileText,
  Map, TreePine, Leaf, Users, Key, RefreshCw, Lock,
  Target, Download, Activity, Database, Globe, Zap, GitBranch,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Features — SusDevOS",
  description:
    "Full Scope 1, 2 and 3 GHG calculations, TNFD biodiversity reporting, Verra/Gold Standard credit validation, GIS land parcel mapping, verification workflow and more — built on GHG Protocol.",
  alternates: { canonical: "https://susdevos.com/features" },
};

// ─────────────────────────────────────────────────────────────────────────────
// Data
// ─────────────────────────────────────────────────────────────────────────────

const FEATURE_GROUPS = [
  {
    id:       "ghg",
    heading:  "GHG Emissions",
    subhead:  "Server-side calculations. No spreadsheet formulas.",
    Icon:     BarChart3,
    color:    "brand",
    features: [
      {
        title: "Scope 1, 2 and 3 — all 15 categories",
        body:  "Every Scope 3 category from the GHG Protocol Corporate Value Chain Standard is supported, with guided relevance assessments and documented materiality decisions.",
      },
      {
        title: "Dual Scope 2 (location-based and market-based)",
        body:  "Both methods are calculated simultaneously for every electricity record. SusDevOS applies the correct grid emission factor automatically based on entity location.",
      },
      {
        title: "IPCC AR6 GWP100 — always current",
        body:  "Global warming potential values from the IPCC Sixth Assessment Report are applied automatically. Switching GWP datasets (AR4, AR5, AR6) recalculates the entire inventory instantly.",
      },
      {
        title: "Multi-gas tracking",
        body:  "CO₂, CH₄, N₂O, HFCs, PFCs and SF₆ are tracked individually with gas-specific factors, then aggregated to CO₂e. Biogenic CO₂ is separately reported per GHG Protocol guidance.",
      },
      {
        title: "Unit conversion pipeline",
        body:  "Enter activity data in any unit — kWh, litres, miles, tonnes, spend. SusDevOS converts to canonical units before applying emission factors. No manual conversion required.",
      },
      {
        title: "Supplier and spend-based Scope 3",
        body:  "Spend-based Scope 3 categories use daily ECB FX rates to convert to USD before applying EXIOBASE spend-based factors. Every conversion rate is stored for audit.",
      },
    ],
  },
  {
    id:       "inventory",
    heading:  "Inventory Management",
    subhead:  "Formal, versioned inventories with a complete calculation trail.",
    Icon:     Database,
    color:    "blue",
    features: [
      {
        title: "Formal GHG inventories",
        body:  "Each reporting year produces a versioned GHGInventory record. Once verified, it becomes immutable — no edits allowed without a new version. Full GHG Protocol conformance.",
      },
      {
        title: "Verification workflow",
        body:  "Internal review → approval → third-party verification sign-off → immutable verified status. Every state transition is logged with the approver's identity and timestamp.",
      },
      {
        title: "Full calculation audit trail",
        body:  "Every emission factor, GWP value, unit conversion, and boundary decision is stored against each record. Verifiers get the full methodology, not just a total.",
      },
      {
        title: "Multi-year tracking",
        body:  "Historical inventories are preserved and unchanged when you update baseline year data. Year-on-year trend analysis is available across all reporting periods.",
      },
      {
        title: "Bulk Excel import",
        body:  "Import multiple emissions records at once via structured Excel templates. Validation errors are reported row-by-row before any data is committed.",
      },
      {
        title: "Organisational boundary setting",
        body:  "Define equity share, financial control, or operational control consolidation approach per entity. Boundary decisions are documented alongside the inventory.",
      },
    ],
  },
  {
    id:       "targets",
    heading:  "Targets & Reporting",
    subhead:  "From inventory to submission-ready report in one step.",
    Icon:     Target,
    color:    "teal",
    features: [
      {
        title: "TNFD LEAP biodiversity reporting",
        body:  "Structure biodiversity impact assessments using the TNFD LEAP (Locate, Evaluate, Assess, Prepare) framework. Species records include IUCN Red List conservation status for full TNFD v1.0 disclosure.",
      },
      {
        title: "Verra/Gold Standard credit validation",
        body:  "Real-time registry check on carbon offset serial numbers against Verra VCS and Gold Standard registries. Unvalidated credits are never deducted from net inventory totals.",
      },
      {
        title: "Formal GHG Protocol PDF report",
        body:  "One click generates a PDF with: reporting boundary, methodology, all emission factors used, GWP dataset, scope totals, and a data quality assessment. Includes page, version, and entity metadata.",
      },
      {
        title: "Carbon offset tracking",
        body:  "Log VCS and Gold Standard carbon credits with serial number validation against the registries. Unvalidated credits are never deducted from net inventory totals.",
      },
      {
        title: "Intensity metrics",
        body:  "Calculate emissions per revenue, per employee, per square metre, or any custom intensity denominator. Track intensity improvements against the same project restoration targets.",
      },
      {
        title: "CSV and JSON export",
        body:  "Raw data export for use in BI tools, board reports, or custom analysis. All exports include the full field set including calculation inputs.",
      },
    ],
  },
  {
    id:       "land",
    heading:  "Land, Ecosystems & Biodiversity",
    subhead:  "For development projects with nature-based impacts.",
    Icon:     TreePine,
    color:    "lime",
    features: [
      {
        title: "GIS land parcel mapping",
        body:  "Record precise boundary geometries (Polygon or MultiPolygon GeoJSON) via interactive map or paste. Boundaries are stored in PostGIS and visualised on an OpenStreetMap layer.",
      },
      {
        title: "IPCC Tier 1, 2 and 3 biomass carbon",
        body:  "Tree removal carbon stock calculations using IPCC 2006 LULUCF biomass tables. Species-specific above-ground biomass, below-ground ratio, and basic wood density pulled from GBIF taxonomy lookup.",
      },
      {
        title: "Habitat restoration sequestration",
        body:  "30-year carbon sequestration projections for restoration activities using IPCC growth curve parameters. Track cumulative sequestration against project-level net-zero targets.",
      },
      {
        title: "TNFD LEAP framework",
        body:  "Structure biodiversity impact assessments using the TNFD LEAP (Locate, Evaluate, Assess, Prepare) framework. Species records include IUCN Red List conservation status.",
      },
      {
        title: "Ecosystem tracking",
        body:  "Record habitat types, area affected, restoration interventions, and species present across all project land parcels. Link parcels to development projects and restoration activities.",
      },
      {
        title: "Project carbon summary reports",
        body:  "Generate project-level carbon reports for planning consents, Environmental Impact Assessments, and green finance documentation.",
      },
    ],
  },
  {
    id:       "multitenancy",
    heading:  "Multi-entity & Collaboration",
    subhead:  "One platform for one entity or fifty client accounts.",
    Icon:     Users,
    color:    "violet",
    features: [
      {
        title: "Multi-tenant row-level isolation",
        body:  "Every query is scoped to the active entity ID set by authenticated middleware. Data from one entity is never visible to another, even from the same account.",
      },
      {
        title: "Role-based access control",
        body:  "Granular privilege system: SuperAdmin, Entity Admin, Manager, Staff. Module-level access control — users only see the modules their role permits. All enforced server-side.",
      },
      {
        title: "Consultant multi-entity management",
        body:  "Switch between client entities from a single login without re-authenticating. Up to 25 entities on Agency plan. Client read-only portal available for sharing results.",
      },
      {
        title: "White-label PDF reports",
        body:  "Agency and Enterprise plans can replace the SusDevOS branding on PDF reports with your firm's logo and brand colours. Client-facing output with your identity.",
      },
      {
        title: "Audit log",
        body:  "Every create, update, delete, state change, and login is logged with user identity, timestamp, and changed values. Retained for 7 years. Exportable for compliance review.",
      },
    ],
  },
  {
    id:       "security",
    heading:  "Security & Compliance",
    subhead:  "Enterprise-grade security without enterprise complexity.",
    Icon:     Shield,
    color:    "slate",
    features: [
      {
        title: "JWT with server-side revocation",
        body:  "15-minute access tokens with 7-day HttpOnly refresh cookies. Revoked tokens are checked against a server-side table (JTI UUID) — logout is immediate even if a token is intercepted.",
      },
      {
        title: "7-year audit log retention",
        body:  "Complete change history retained for 7 years. Log entries are immutable — not even admins can delete them. GDPR compliant. Exportable on request.",
      },
      {
        title: "Verified inventories are immutable",
        body:  "Once a GHG inventory reaches verification status ≥ 3, all edit operations are rejected with HTTP 403. Corrections require a formal amended inventory.",
      },
      {
        title: "ISO 27001 roadmap",
        body:  "Cyber Essentials certified. ISO 27001 certification in progress. Annual penetration testing. Vulnerability disclosure program. SOC 2 Type II on the Enterprise roadmap.",
      },
      {
        title: "GDPR compliant",
        body:  "Data residency in UK/EU. DPA available for all paid plans. Right to erasure implemented. No personal data sent to external APIs — only company registration numbers, activity types, and species names.",
      },
      {
        title: "Zero client-side calculations",
        body:  "All GHG calculations happen server-side. Client-submitted emission amounts are silently ignored and overwritten. Calculations cannot be tampered with by browser tooling.",
      },
    ],
  },
];

const COLOR_MAP: Record<string, { icon: string; light: string; border: string }> = {
  brand:  { icon: "text-brand-600",   light: "bg-brand-50",   border: "border-brand-100"  },
  blue:   { icon: "text-blue-600",    light: "bg-blue-50",    border: "border-blue-100"   },
  teal:   { icon: "text-teal-600",    light: "bg-teal-50",    border: "border-teal-100"   },
  lime:   { icon: "text-lime-700",    light: "bg-lime-50",    border: "border-lime-100"   },
  violet: { icon: "text-violet-600",  light: "bg-violet-50",  border: "border-violet-100" },
  slate:  { icon: "text-surface-600", light: "bg-surface-100", border: "border-surface-200" },
};

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
          Product features
        </p>
        <h1 className="mx-auto mb-5 max-w-3xl text-4xl font-bold text-white sm:text-5xl lg:text-6xl leading-tight">
          Everything your GHG inventory{" "}
          <span
            className="text-transparent"
            style={{
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              backgroundImage: "linear-gradient(135deg, #4ade80 0%, #2dd4bf 100%)",
            }}
          >
            actually needs
          </span>
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-lg text-surface-300 leading-relaxed">
          Built on GHG Protocol and IPCC methodology. Every calculation is server-side,
          every factor is sourced from authoritative datasets, and every number has a full audit trail.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-500/25 transition-colors hover:bg-brand-400"
          >
            Start for free <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-white/20"
          >
            Book a demo
          </Link>
        </div>

        {/* Quick stat strip */}
        <div className="mx-auto mt-14 grid max-w-3xl grid-cols-2 gap-4 border-t border-white/10 pt-10 sm:grid-cols-4">
          {[
            { n: "6",       l: "Feature areas"          },
            { n: "All 15",  l: "Scope 3 categories"     },
            { n: "Dual",    l: "Scope 2 methods"        },
            { n: "7-year",  l: "Audit retention"        },
          ].map(({ n, l }) => (
            <div key={l} className="text-center">
              <p className="text-2xl font-bold text-white">{n}</p>
              <p className="mt-0.5 text-xs text-surface-400">{l}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function FeatureGroup({
  id, heading, subhead, Icon, color, features,
}: typeof FEATURE_GROUPS[0]) {
  const c = COLOR_MAP[color];
  return (
    <section id={id} className="scroll-mt-20 py-16 sm:py-20 even:bg-surface-50 odd:bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 flex items-start gap-4">
          <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${c.light} border ${c.border}`}>
            <Icon className={`h-5 w-5 ${c.icon}`} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-surface-900 sm:text-3xl">{heading}</h2>
            <p className="mt-1 text-surface-500">{subhead}</p>
          </div>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ title, body }) => (
            <div
              key={title}
              className="rounded-xl border border-surface-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className={`mb-3 inline-flex items-center justify-center rounded-lg p-1.5 ${c.light}`}>
                <CheckCircle2 className={`h-4 w-4 ${c.icon}`} />
              </div>
              <h3 className="mb-2 font-semibold text-surface-900">{title}</h3>
              <p className="text-sm leading-relaxed text-surface-500">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

function JumpNav() {
  return (
    <nav className="sticky top-[65px] z-40 border-b border-surface-200 bg-white/95 backdrop-blur-md">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="flex gap-0 overflow-x-auto">
          {FEATURE_GROUPS.map(({ id, heading }) => (
            <a
              key={id}
              href={`#${id}`}
              className="shrink-0 border-b-2 border-transparent px-4 py-3 text-sm text-surface-500 transition-colors hover:border-brand-500 hover:text-surface-900"
            >
              {heading}
            </a>
          ))}
        </div>
      </div>
    </nav>
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
          Ready to see it in action?
        </h2>
        <p className="mx-auto mb-8 max-w-lg text-brand-100">
          Free plan available. No credit card required. Full feature access on the 14-day trial.
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

export default function FeaturesPage() {
  return (
    <>
      <Hero />
      <JumpNav />
      {FEATURE_GROUPS.map((group) => (
        <FeatureGroup key={group.id} {...group} />
      ))}
      <CTA />
    </>
  );
}

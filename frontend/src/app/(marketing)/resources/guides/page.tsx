import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Database,
  TreePine,
  Target,
  Leaf,
  FileText,
  CreditCard,
  Map,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Guides — SusDevOS",
  description:
    "Step-by-step guides for GHG emissions recording, Scope 2 dual method, GHG inventories, land parcel mapping, biomass carbon, carbon offsets, TNFD biodiversity, targets, and reports.",
  alternates: { canonical: "https://susdevos.com/resources/guides" },
};

// ─────────────────────────────────────────────────────────────────────────────
// Guide data
// ─────────────────────────────────────────────────────────────────────────────

const GUIDES = [
  {
    slug: "recording-ghg-emissions",
    Icon: BarChart3,
    color: "brand",
    badge: "GHG Emissions",
    title: "Recording GHG Emissions (Scope 1, 2, 3)",
    summary:
      "How to log activity data, choose the right emission factor, and let SusDevOS calculate your tCO₂e — across all three scopes and all 15 Scope 3 categories.",
    time: "8 min read",
  },
  {
    slug: "scope-2-dual-method",
    Icon: BarChart3,
    color: "blue",
    badge: "GHG Emissions",
    title: "Scope 2 Dual Method: Location-Based vs Market-Based",
    summary:
      "Understand why both methods are required, when each applies, and how SusDevOS calculates both simultaneously for every electricity record.",
    time: "5 min read",
  },
  {
    slug: "ghg-inventories",
    Icon: Database,
    color: "blue",
    badge: "Inventories",
    title: "Building and Verifying a GHG Inventory",
    summary:
      "Create a formal annual inventory, add emissions records, move through the verification workflow, and generate a GHG Protocol-conformant PDF report.",
    time: "10 min read",
  },
  {
    slug: "land-parcels-ecosystem",
    Icon: Map,
    color: "lime",
    badge: "Land & Nature",
    title: "Land Parcels and Ecosystem Tracking",
    summary:
      "Record precise GeoJSON boundaries, link parcels to development projects, log habitat types, and track ecosystem changes across your portfolio.",
    time: "6 min read",
  },
  {
    slug: "biomass-carbon-tree-removals",
    Icon: TreePine,
    color: "lime",
    badge: "Land & Nature",
    title: "Biomass Carbon and Tree Removals (IPCC LULUCF)",
    summary:
      "How SusDevOS uses IPCC Tier 1/2/3 biomass tables to calculate carbon stock loss from tree removals and 30-year sequestration projections for restoration activities.",
    time: "7 min read",
  },
  {
    slug: "carbon-offsets-validation",
    Icon: CreditCard,
    color: "teal",
    badge: "Carbon Credits",
    title: "Carbon Offsets and Verra/Gold Standard Validation",
    summary:
      "Log VCS and Gold Standard carbon credits, validate serial numbers against the live registries, and understand how validated credits affect your net inventory total.",
    time: "5 min read",
  },
  {
    slug: "tnfd-biodiversity",
    Icon: Leaf,
    color: "lime",
    badge: "Biodiversity",
    title: "TNFD Biodiversity Reporting and Species Tracking",
    summary:
      "Use the TNFD LEAP framework to structure biodiversity impact assessments, track species with IUCN Red List status, and generate TNFD-aligned disclosures.",
    time: "7 min read",
  },
  {
    slug: "targets-milestones",
    Icon: Target,
    color: "teal",
    badge: "Targets",
    title: "Setting Targets and Tracking Milestones",
    summary:
      "Create emissions reduction or sequestration targets, add interim milestones, and track progress against baseline figures from your verified inventories.",
    time: "4 min read",
  },
  {
    slug: "reports-exports",
    Icon: FileText,
    color: "slate",
    badge: "Reports",
    title: "Generating Reports and Exporting Data",
    summary:
      "Produce a GHG Protocol PDF report in one click, export raw data to CSV or JSON, and understand what each report field contains.",
    time: "4 min read",
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Colour helpers
// ─────────────────────────────────────────────────────────────────────────────

const ICON_BG: Record<string, string> = {
  brand: "bg-brand-500/10 text-brand-500",
  blue: "bg-blue-500/10 text-blue-400",
  teal: "bg-teal-500/10 text-teal-400",
  lime: "bg-lime-500/10 text-lime-400",
  slate: "bg-slate-500/10 text-slate-400",
};

const BADGE_COLOR: Record<string, string> = {
  "GHG Emissions": "bg-blue-500/10 text-blue-300 border border-blue-500/20",
  Inventories: "bg-brand-500/10 text-brand-300 border border-brand-500/20",
  "Land & Nature": "bg-lime-500/10 text-lime-300 border border-lime-500/20",
  "Carbon Credits": "bg-teal-500/10 text-teal-300 border border-teal-500/20",
  Biodiversity: "bg-lime-500/10 text-lime-300 border border-lime-500/20",
  Targets: "bg-teal-500/10 text-teal-300 border border-teal-500/20",
  Reports: "bg-slate-500/10 text-slate-300 border border-slate-500/20",
};

// ─────────────────────────────────────────────────────────────────────────────
// Components
// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-24"
      style={{
        background: [
          "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(22,163,74,0.12) 0%, transparent 70%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-brand-400">
          Resources
        </p>
        <h1 className="mb-4 text-4xl font-bold text-white sm:text-5xl">
          Guides
        </h1>
        <p className="mx-auto max-w-xl text-lg text-surface-300">
          Step-by-step walkthroughs for every feature — from your first
          emissions record to a verified, report-ready GHG inventory.
        </p>
      </div>
    </section>
  );
}

function GuideCard({ guide }: { guide: (typeof GUIDES)[number] }) {
  const { Icon, color, badge, title, summary, time, slug } = guide;
  return (
    <Link
      href={`/resources/guides/${slug}`}
      className="group flex flex-col gap-4 rounded-xl border border-surface-700 bg-surface-800 p-6 transition hover:border-brand-500/50 hover:bg-surface-700/60"
    >
      <div className="flex items-start justify-between gap-4">
        <div
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${ICON_BG[color]}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE_COLOR[badge]}`}
        >
          {badge}
        </span>
      </div>
      <div className="flex-1">
        <h2 className="mb-2 text-base font-semibold text-white group-hover:text-brand-300 transition-colors">
          {title}
        </h2>
        <p className="text-sm leading-relaxed text-surface-400">{summary}</p>
      </div>
      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-surface-500">{time}</span>
        <ArrowRight className="h-4 w-4 text-surface-500 transition-transform group-hover:translate-x-1 group-hover:text-brand-400" />
      </div>
    </Link>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function GuidesPage() {
  return (
    <>
      <Hero />

      <section className="bg-surface-900 py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {GUIDES.map((g) => (
              <GuideCard key={g.slug} guide={g} />
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bg-surface-900 py-12 border-t border-surface-800">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 flex flex-col items-center text-center gap-4">
          <p className="text-surface-400 text-sm">
            Can&rsquo;t find what you&rsquo;re looking for?
          </p>
          <Link
            href="/contact"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-500 transition-colors"
          >
            Contact support <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </>
  );
}

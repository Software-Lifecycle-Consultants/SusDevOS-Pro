import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Zap, RefreshCw, Shield } from "lucide-react";
import { IntegrationsGrid } from "./IntegrationsGrid";

export const metadata: Metadata = {
  title: "Integrations — SusDevOS",
  description:
    "SusDevOS connects to 12 authoritative data sources — automatically syncing emission factors, validating carbon credits, and enriching entity data. DEFRA, EPA eGRID, Climatiq, Verra, GBIF and more.",
};

// ─────────────────────────────────────────────────────────────────────────────
// Hero
// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-28"
      style={{
        background: [
          "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(22,163,74,0.15) 0%, transparent 70%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-sm text-brand-300">
          12 live integrations
        </div>
        <h1 className="mx-auto mb-5 max-w-3xl text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
          Connected to the data sources{" "}
          <span
            className="text-transparent"
            style={{
              backgroundClip: "text",
              WebkitBackgroundClip: "text",
              backgroundImage: "linear-gradient(135deg, #4ade80 0%, #2dd4bf 100%)",
            }}
          >
            your verifier uses
          </span>
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-lg leading-relaxed text-surface-300">
          SusDevOS integrates with 12 authoritative data providers — automatically syncing
          emission factors, validating carbon credits, and enriching entity data so you
          never have to look anything up manually.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-500/25 transition-colors hover:bg-brand-400"
          >
            Start for free
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-white/20"
          >
            Book a demo
          </Link>
        </div>

        {/* Quick stats */}
        <div className="mx-auto mt-12 grid max-w-2xl grid-cols-3 gap-6 border-t border-white/10 pt-10">
          {[
            { number: "12",     label: "Data providers"       },
            { number: "Daily",  label: "FX rate updates"      },
            { number: "Auto",   label: "No manual data entry" },
          ].map(({ number, label }) => (
            <div key={label} className="text-center">
              <p className="text-2xl font-bold text-white">{number}</p>
              <p className="mt-0.5 text-xs text-surface-400">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// How data flows
// ─────────────────────────────────────────────────────────────────────────────

const PATTERNS = [
  {
    Icon:    Zap,
    title:   "On-demand",
    color:   "bg-surface-100 text-surface-700",
    iconCls: "bg-surface-200 text-surface-700",
    steps:   [
      "User enters data in SusDevOS",
      "Platform calls external API in real time",
      "Response validated and cached to database",
      "Data available immediately in your record",
    ],
    examples: "Companies House · GBIF · IUCN · Verra · Gold Standard",
    note:    "Results are cached so repeat lookups are instant. External APIs are called only once per unique query.",
  },
  {
    Icon:    RefreshCw,
    title:   "Scheduled sync",
    color:   "bg-brand-50 text-brand-700",
    iconCls: "bg-brand-100 text-brand-700",
    steps:   [
      "Celery beat triggers on fixed schedule",
      "External source downloaded or queried",
      "Data parsed and upserted into platform tables",
      "New factors and rates available automatically",
    ],
    examples: "DEFRA · EPA eGRID · Climatiq · SBTi · ECB · Verra cache",
    note:    "Scheduled syncs run in the background without interrupting your work. You always have current data.",
  },
  {
    Icon:    Shield,
    title:   "Never auto-applied",
    color:   "bg-amber-50 text-amber-700",
    iconCls: "bg-amber-100 text-amber-700",
    steps:   [
      "Integration returns candidate data",
      "SusDevOS presents results for review",
      "User confirms before any record is saved",
      "Confirmed data applied — full audit trail",
    ],
    examples: "Companies House · OpenCorporates · Species lookup",
    note:    "Entity auto-population always requires user confirmation. We never silently overwrite your data.",
  },
];

function DataFlowSection() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">How it works</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            Three integration patterns
          </h2>
          <p className="mt-4 text-surface-500">
            Every integration follows one of these patterns, so you always know when and how your data is updated.
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-3">
          {PATTERNS.map(({ Icon, title, color, iconCls, steps, examples, note }) => (
            <div key={title} className="rounded-2xl border border-surface-200 bg-white p-7">
              <div className={`mb-5 inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-sm font-semibold ${color}`}>
                <Icon className="h-3.5 w-3.5" />
                {title}
              </div>

              {/* Steps */}
              <ol className="mb-5 space-y-3">
                {steps.map((step, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${iconCls}`}>
                      {i + 1}
                    </span>
                    <span className="text-sm leading-snug text-surface-600">{step}</span>
                  </li>
                ))}
              </ol>

              <div className="space-y-3 border-t border-surface-100 pt-4">
                <div>
                  <p className="mb-1 text-[10px] font-bold uppercase tracking-widest text-surface-400">Used by</p>
                  <p className="text-xs text-surface-500">{examples}</p>
                </div>
                <p className="text-xs italic text-surface-400">{note}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Privacy note
// ─────────────────────────────────────────────────────────────────────────────

function PrivacyNote() {
  return (
    <section className="bg-white py-14">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto max-w-3xl rounded-2xl border border-surface-200 bg-surface-50 p-8 text-center">
          <Shield className="mx-auto mb-4 h-8 w-8 text-surface-400" />
          <h3 className="mb-3 text-lg font-semibold text-surface-900">No personal data leaves the platform</h3>
          <p className="text-sm leading-relaxed text-surface-500">
            All external API queries use company names, registration numbers, activity types, species names,
            and serial numbers only — never personal data. FX rates, DEFRA factors, and GBIF taxonomy
            are public data cached locally. Climatiq is a paid service — raw API responses are never
            exposed to unauthenticated endpoints.
          </p>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CTA
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
          All 12 integrations. Free to start.
        </h2>
        <p className="mx-auto mb-8 max-w-lg text-brand-100">
          Every integration listed here is available on all plans, including the free tier.
          No API keys to manage — we handle the connections.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-brand-700 shadow-lg transition-colors hover:bg-brand-50"
          >
            Start for free — no credit card
            <ArrowRight className="h-4 w-4" />
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
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  return (
    <>
      <Hero />
      <IntegrationsGrid />
      <DataFlowSection />
      <PrivacyNote />
      <CTA />
    </>
  );
}

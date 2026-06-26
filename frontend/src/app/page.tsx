import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight, CheckCircle2, BarChart3, Leaf,
  Shield, BookOpen, Database, Globe, FileText,
  TrendingDown, Zap, Lock, RefreshCw,
} from "lucide-react";
import { NavBar }          from "@/components/marketing/NavBar";
import { Footer }          from "@/components/marketing/Footer";
import { FeatureTabs }     from "@/components/marketing/FeatureTabs";
import { CarbonEstimator } from "@/components/marketing/CarbonEstimator";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://susdevos.com";

export const metadata: Metadata = {
  title: "SusDevOS — GHG Reporting & Ecosystem Tracking for Development Projects",
  description:
    "Calculate your Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate GHG Protocol-conformant reports. Free to start. Built for TNFD, ecosystem MRV, and nature-based carbon.",
  keywords:
    "GHG reporting software, carbon footprint calculator, Scope 3 emissions, TNFD biodiversity, ecosystem MRV, nature-based carbon, emissions inventory",
  alternates: {
    canonical: SITE_URL,
    types: { "application/rss+xml": `${SITE_URL}/rss.xml` },
  },
  openGraph: {
    title:       "SusDevOS — GHG Reporting & Ecosystem Tracking",
    description: "Calculate Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate audit-ready GHG reports. Free to start.",
    type:        "website",
    url:         SITE_URL,
    siteName:    "SusDevOS",
  },
  twitter: {
    card:        "summary_large_image",
    title:       "SusDevOS — GHG Reporting & Ecosystem Tracking",
    description: "Calculate Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate audit-ready GHG reports.",
  },
};

function OrganizationJsonLd() {
  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type":       "Organization",
        "@id":         `${SITE_URL}/#organization`,
        "name":        "SusDevOS",
        "url":         SITE_URL,
        "description": "GHG reporting and ecosystem tracking software built on GHG Protocol, IPCC, Verra, and TNFD.",
        "sameAs": [
          "https://linkedin.com/company/susdevos",
          "https://github.com/susdevos",
        ],
      },
      {
        "@type":           "WebSite",
        "@id":             `${SITE_URL}/#website`,
        "url":             SITE_URL,
        "name":            "SusDevOS",
        "publisher":       { "@id": `${SITE_URL}/#organization` },
        "potentialAction": {
          "@type":       "SearchAction",
          "target":      { "@type": "EntryPoint", "urlTemplate": `${SITE_URL}/blog?q={search_term_string}` },
          "query-input": "required name=search_term_string",
        },
      },
    ],
  };
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Hero
// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-24 sm:py-32"
      style={{
        background: [
          "radial-gradient(ellipse 90% 70% at 50% -5%, rgba(22,163,74,0.18) 0%, transparent 70%)",
          "radial-gradient(ellipse 50% 50% at 95% 60%, rgba(5,150,105,0.1) 0%, transparent 60%)",
          "#0f172a",
        ].join(", "),
      }}
    >
      {/* Dot grid */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.07) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid items-center gap-16 lg:grid-cols-2">

          {/* ── Copy ── */}
          <div>
            {/* Badge */}
            <Link
              href="/changelog"
              className="mb-8 inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-sm text-brand-300 transition-colors hover:bg-brand-500/20"
            >
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand-400" />
              TNFD v1.0 LEAP framework support now available →
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>

            <h1 className="mb-6 text-5xl font-bold leading-[1.08] tracking-tight text-white sm:text-6xl">
              Your GHG inventory.{" "}
              <span
                className="text-transparent"
                style={{
                  backgroundClip: "text",
                  WebkitBackgroundClip: "text",
                  backgroundImage: "linear-gradient(135deg, #4ade80 0%, #2dd4bf 100%)",
                }}
              >
                Verified. Ready.
              </span>
            </h1>

            <p className="mb-8 max-w-lg text-lg leading-relaxed text-surface-300">
              Calculate Scope 1, 2 and 3 emissions. Track ecosystem impacts.
              Generate audit-ready reports aligned to GHG Protocol, Verra/Gold Standard, and TNFD.
            </p>

            <div className="mb-6 flex flex-wrap gap-3">
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

            <div className="flex flex-wrap gap-x-5 gap-y-2">
              {["No credit card required", "Free forever plan", "Set up in under 5 minutes"].map((t) => (
                <span key={t} className="flex items-center gap-1.5 text-sm text-surface-400">
                  <CheckCircle2 className="h-3.5 w-3.5 text-brand-500" />
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* ── App mockup ── */}
          <div className="relative hidden lg:block">
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-surface-800/70 shadow-2xl ring-1 ring-white/5 backdrop-blur-sm">
              {/* Browser chrome */}
              <div className="flex items-center gap-2 border-b border-white/10 bg-surface-900/60 px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-red-500/60" />
                  <div className="h-3 w-3 rounded-full bg-amber-500/60" />
                  <div className="h-3 w-3 rounded-full bg-brand-500/60" />
                </div>
                <div className="mx-3 flex-1 rounded-md bg-surface-900/60 px-3 py-1 text-xs text-surface-500">
                  app.susdevos.com/inventories/2024
                </div>
              </div>

              {/* Dashboard content */}
              <div className="p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-surface-500">GHG Inventory · FY 2024</p>
                    <p className="mt-0.5 text-base font-semibold text-white">Acme Property Group</p>
                  </div>
                  <div className="flex items-center gap-1.5 rounded-full border border-brand-500/30 bg-brand-500/15 px-3 py-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-brand-400" />
                    <span className="text-xs font-medium text-brand-400">Verified</span>
                  </div>
                </div>

                <div className="mb-5 space-y-4">
                  {[
                    { label: "Scope 1 — Direct combustion",     value: "847",   pct: 15,  bar: "bg-brand-500" },
                    { label: "Scope 2 — Purchased electricity",  value: "1,234", pct: 22,  bar: "bg-teal-400"  },
                    { label: "Scope 3 — Value chain",            value: "3,891", pct: 63,  bar: "bg-cyan-400"  },
                  ].map(({ label, value, pct, bar }) => (
                    <div key={label}>
                      <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-xs text-surface-400">{label}</span>
                        <span className="font-mono text-xs font-medium text-white">
                          {value} <span className="text-surface-500">tCO₂e</span>
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-surface-700">
                        <div className={`h-full rounded-full ${bar}`} style={{ width: `${pct * 1.3}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-between rounded-xl border border-white/5 bg-surface-900/50 px-4 py-3">
                  <div>
                    <p className="text-xs text-surface-500">Net total</p>
                    <p className="text-2xl font-bold tabular-nums text-white">
                      5,972 <span className="text-sm font-normal text-surface-400">tCO₂e</span>
                    </p>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-lg border border-brand-500/20 bg-brand-500/10 px-3 py-1.5 text-sm font-semibold text-brand-400">
                    <TrendingDown className="h-3.5 w-3.5" />
                    ↓ 18.4% vs baseline
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-white/5 bg-surface-900/40 p-3">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-surface-500">Net Zero target</p>
                    <p className="mt-0.5 text-xs font-semibold text-white">On track · 2040 goal</p>
                  </div>
                  <div className="rounded-lg border border-white/5 bg-surface-900/40 p-3">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-surface-500">Report ready</p>
                    <p className="mt-0.5 text-xs font-semibold text-white">TNFD · Verra · GHG Protocol</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating chip — verification status */}
            <div className="absolute -bottom-5 -left-8 flex items-center gap-3 rounded-xl border border-white/10 bg-surface-900 px-4 py-3 shadow-2xl">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500/20">
                <CheckCircle2 className="h-4 w-4 text-brand-400" />
              </div>
              <div>
                <p className="text-[10px] font-medium uppercase tracking-wider text-surface-500">3rd-party verified</p>
                <p className="text-xs font-semibold text-white">Immutable audit trail</p>
              </div>
            </div>

            {/* Floating chip — data source */}
            <div className="absolute -right-6 -top-5 flex items-center gap-3 rounded-xl border border-white/10 bg-surface-900 px-4 py-3 shadow-2xl">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/20">
                <Database className="h-4 w-4 text-blue-400" />
              </div>
              <div>
                <p className="text-[10px] font-medium uppercase tracking-wider text-surface-500">Emission factors</p>
                <p className="text-xs font-semibold text-white">DEFRA 2024 · Climatiq</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Standards / Trust bar
// ─────────────────────────────────────────────────────────────────────────────

const STANDARDS = [
  { abbr: "GHG Protocol", note: "All 15 Scope 3 categories"    },
  { abbr: "TNFD",         note: "LEAP framework aligned"       },
  { abbr: "IPCC AR6",     note: "GWP100 & LULUCF biomass"     },
  { abbr: "Verra VCS",    note: "Carbon credit validation"     },
  { abbr: "Gold Standard",note: "Credit registry validation"   },
  { abbr: "UN SDGs",      note: "SDG 13, 15, 7 & 11 mapping"  },
];

function TrustBar() {
  return (
    <section className="border-y border-surface-100 bg-white py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="mb-8 text-center text-xs font-medium uppercase tracking-widest text-surface-400">
          Aligned to the standards that matter
        </p>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6">
          {STANDARDS.map(({ abbr, note }) => (
            <div key={abbr} className="text-center">
              <p className="text-sm font-bold text-surface-800">{abbr}</p>
              <p className="mt-0.5 text-xs leading-snug text-surface-400">{note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Stats
// ─────────────────────────────────────────────────────────────────────────────

const STATS = [
  { number: "10,000+", label: "Emission factors",    sub: "DEFRA, EPA, Climatiq"       },
  { number: "All 15",  label: "Scope 3 categories",  sub: "GHG Protocol complete"      },
  { number: "Dual",    label: "Scope 2 methods",      sub: "Location & market-based"    },
  { number: "7-year",  label: "Audit log retention",  sub: "GDPR & ISO 27001 aligned"  },
];

function StatsSection() {
  return (
    <section className="bg-brand-950 py-14">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {STATS.map(({ number, label, sub }) => (
            <div key={label} className="text-center">
              <p className="text-3xl font-bold text-white sm:text-4xl">{number}</p>
              <p className="mt-1.5 text-sm font-semibold text-brand-200">{label}</p>
              <p className="mt-0.5 text-xs text-brand-400">{sub}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Problem section
// ─────────────────────────────────────────────────────────────────────────────

const PROBLEMS = [
  {
    Icon:  Database,
    title: '"Our data is all over the place."',
    body:  "Activity data in one spreadsheet, emission factors in another, reports emailed as PDFs. One wrong formula corrupts the whole inventory.",
  },
  {
    Icon:  Shield,
    title: '"We can\'t prove our numbers."',
    body:  "Auditors need a full calculation trail. Spreadsheets provide none, and recreating the methodology during a review takes weeks.",
  },
  {
    Icon:  BookOpen,
    title: '"It takes months every year."',
    body:  "Manual data collection, chasing suppliers for Scope 3, formatting reports. The same work, repeated annually, with no institutional memory.",
  },
];

function ProblemSection() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 max-w-2xl">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">The problem</p>
          <h2 className="text-3xl font-bold leading-tight text-surface-900 sm:text-4xl">
            Most sustainability teams are still working in Excel.{" "}
            <span className="text-surface-400">That&apos;s a problem.</span>
          </h2>
        </div>
        <div className="grid gap-5 sm:grid-cols-3">
          {PROBLEMS.map(({ Icon, title, body }) => (
            <div
              key={title}
              className="group rounded-2xl border border-surface-200 bg-white p-7 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-red-50">
                <Icon className="h-5 w-5 text-red-500" />
              </div>
              <h3 className="mb-2.5 font-semibold leading-snug text-surface-900">{title}</h3>
              <p className="text-sm leading-relaxed text-surface-500">{body}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 text-center">
          <p className="text-lg font-semibold text-surface-700">
            SusDevOS solves all three —{" "}
            <Link href="/register" className="text-brand-600 underline underline-offset-4 hover:text-brand-700">
              free to start
            </Link>
            .
          </p>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// How it works
// ─────────────────────────────────────────────────────────────────────────────

const STEPS = [
  {
    number: "01",
    title:  "Enter your activity data",
    body:   "Fuel use, electricity, travel, purchased goods — in the units you already have. Emission factors from DEFRA, EPA and Climatiq apply automatically. No formula required.",
  },
  {
    number: "02",
    title:  "Review your calculated inventory",
    body:   "See Scope 1, 2 and 3 totals in real time. Both Scope 2 methods calculated simultaneously. Track restoration sequestration and TNFD metrics. Flag data quality issues before they become audit findings.",
  },
  {
    number: "03",
    title:  "Generate and submit your report",
    body:   "One click produces a GHG Protocol-conformant PDF, ready for your verifier, Verra/Gold Standard, or TNFD disclosure. Every emission factor and GWP value is included and documented.",
  },
];

function HowItWorks() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-16 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">How it works</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            From activity data to verified report in three steps
          </h2>
          <p className="mt-4 text-surface-500">No configuration. No consultant required. Start entering data on day one.</p>
        </div>

        <div className="relative grid gap-10 sm:grid-cols-3">
          {/* Connecting line */}
          <div className="absolute left-0 right-0 top-10 hidden h-px bg-surface-100 sm:block" />

          {STEPS.map(({ number, title, body }) => (
            <div key={number} className="relative">
              <div className="relative mb-6 inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-surface-50 ring-1 ring-surface-200">
                <span className="text-4xl font-black text-brand-100">{number}</span>
              </div>
              <h3 className="mb-2.5 text-lg font-semibold text-surface-900">{title}</h3>
              <p className="text-sm leading-relaxed text-surface-500">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Features
// ─────────────────────────────────────────────────────────────────────────────

function FeaturesSection() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 max-w-2xl">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">Built for your role</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            Every workflow, one platform
          </h2>
          <p className="mt-4 text-surface-500">
            Whether you&apos;re managing one entity or thirty client accounts, SusDevOS adapts to your workflow.
          </p>
        </div>
        <FeatureTabs />
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Before / After comparison
// ─────────────────────────────────────────────────────────────────────────────

const COMPARISON = [
  { before: "Manual emission factor lookup each cycle",         after: "10,000+ factors applied automatically"        },
  { before: "No calculation audit trail",                      after: "Full methodology documented for every record"  },
  { before: "Scope 3 guesswork and partial coverage",          after: "All 15 categories guided, relevance documented"},
  { before: "Annual copy-paste from previous year's workbook", after: "One-click year-on-year rollover"               },
  { before: "PDF reports built manually over days",            after: "Verra/Gold Standard credit validation in seconds" },
  { before: "Formula errors found during verification",        after: "Server-side calculation, no client formulas"   },
];

function ComparisonSection() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">Why switch</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            SusDevOS vs spreadsheets
          </h2>
        </div>
        <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-surface-200 shadow-sm">
          {/* Header */}
          <div className="grid grid-cols-2 border-b border-surface-200 bg-surface-50">
            <div className="px-6 py-4">
              <p className="text-xs font-bold uppercase tracking-widest text-red-500">Without SusDevOS</p>
            </div>
            <div className="border-l border-surface-200 bg-brand-50 px-6 py-4">
              <p className="text-xs font-bold uppercase tracking-widest text-brand-600">With SusDevOS</p>
            </div>
          </div>
          {/* Rows */}
          {COMPARISON.map(({ before, after }, i) => (
            <div
              key={i}
              className={`grid grid-cols-2 ${i < COMPARISON.length - 1 ? "border-b border-surface-100" : ""}`}
            >
              <div className="flex items-start gap-3 px-6 py-4">
                <span className="mt-0.5 shrink-0 text-base text-red-400">✕</span>
                <span className="text-sm leading-relaxed text-surface-500">{before}</span>
              </div>
              <div className="flex items-start gap-3 border-l border-surface-100 bg-brand-50/40 px-6 py-4">
                <span className="mt-0.5 shrink-0 text-base text-brand-500">✓</span>
                <span className="text-sm leading-relaxed text-surface-700">{after}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Data sources
// ─────────────────────────────────────────────────────────────────────────────

const DATA_SOURCES = [
  { name: "DEFRA",       desc: "UK Government GHG conversion factors — updated annually",        dot: "bg-blue-500"    },
  { name: "EPA eGRID",   desc: "US electricity grid emission rates by subregion",                dot: "bg-indigo-500"  },
  { name: "IPCC 2006",   desc: "LULUCF biomass carbon stock tables and growth parameters",       dot: "bg-brand-500"   },
  { name: "Climatiq",    desc: "Global emission factor aggregator with 50,000+ factors",         dot: "bg-teal-500"    },
  { name: "Verra VCS",   desc: "Voluntary carbon credit registry — retirement validation",       dot: "bg-emerald-600" },
  { name: "GBIF / IUCN", desc: "Biodiversity taxonomy and species conservation status",          dot: "bg-lime-600"    },
  { name: "ECB",         desc: "Daily FX rates for spend-based multi-currency Scope 3",         dot: "bg-amber-500"   },
];

function DataSources() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">Data integrity</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            Built on authoritative data sources
          </h2>
          <p className="mt-4 text-surface-500">
            Your emission factors, offset validations and biodiversity records come from the same
            databases your verifier and regulator use.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {DATA_SOURCES.map(({ name, desc, dot }) => (
            <div
              key={name}
              className="group rounded-xl border border-surface-200 bg-white p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className="mb-3 flex items-center gap-2.5">
                <span className={`h-2.5 w-2.5 rounded-full ${dot} shrink-0`} />
                <p className="text-sm font-bold text-surface-800">{name}</p>
              </div>
              <p className="text-xs leading-relaxed text-surface-500">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Carbon estimator
// ─────────────────────────────────────────────────────────────────────────────

function EstimatorSection() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-600">Quick estimate</p>
          <h2 className="text-3xl font-bold text-surface-900 sm:text-4xl">
            How big is your carbon footprint?
          </h2>
          <p className="mt-4 text-surface-500">Find out in 60 seconds. Three questions — we do the maths.</p>
        </div>
        <CarbonEstimator />
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Security / trust
// ─────────────────────────────────────────────────────────────────────────────

const SECURITY_ITEMS = [
  { Icon: Lock,      title: "JWT + server-side revocation",   body: "15-minute access tokens with HttpOnly refresh cookies. No client-side token storage." },
  { Icon: Shield,    title: "Row-level tenant isolation",      body: "Every query scoped to your entity ID. Multi-tenant architecture — your data is never shared." },
  { Icon: RefreshCw, title: "7-year audit log retention",      body: "Every calculation, edit and verification event is logged and immutable. GDPR compliant." },
  { Icon: Zap,       title: "ISO 27001 roadmap",               body: "Cyber Essentials certified. ISO 27001 certification in progress. Annual penetration testing." },
];

function SecuritySection() {
  return (
    <section className="bg-surface-900 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 max-w-2xl">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-400">Security & compliance</p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Enterprise-grade security, built in from day one
          </h2>
          <p className="mt-4 text-surface-400">
            Your sustainability data is sensitive. We treat it that way.
          </p>
        </div>
        <div className="grid gap-5 sm:grid-cols-2">
          {SECURITY_ITEMS.map(({ Icon, title, body }) => (
            <div key={title} className="rounded-2xl border border-white/10 bg-surface-800/50 p-6">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/20">
                <Icon className="h-5 w-5 text-brand-400" />
              </div>
              <h3 className="mb-1.5 font-semibold text-white">{title}</h3>
              <p className="text-sm leading-relaxed text-surface-400">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Pricing teaser
// ─────────────────────────────────────────────────────────────────────────────

const PLANS = [
  {
    name:      "Free",
    price:     "£0",
    note:      "forever",
    highlight: false,
    features:  [
      "1 entity · 1 user",
      "Scope 1 + 2 (location-based)",
      "DEFRA emission factors",
      "Watermarked PDF report",
      "30-day audit log",
    ],
    cta: { label: "Start for free", href: "/register" },
  },
  {
    name:      "Starter",
    price:     "£49",
    note:      "/ month",
    highlight: true,
    features:  [
      "1 entity · 5 users",
      "All scopes — full Scope 3",
      "All emission factor libraries",
      "Formal inventory + carbon goals",
      "CSV / JSON export",
    ],
    cta: { label: "Start 14-day trial", href: "/register?plan=starter" },
  },
  {
    name:      "Professional",
    price:     "£199",
    note:      "/ month",
    highlight: false,
    features:  [
      "5 entities · 20 users",
      "Verification workflow + TNFD",
      "GIS land parcel mapping",
      "IPCC Tier 2/3 biomass",
      "API access · bulk import",
    ],
    cta: { label: "Start 14-day trial", href: "/register?plan=professional" },
  },
];

function PricingTeaser() {
  return (
    <section className="bg-surface-950 py-20 sm:py-24" style={{ background: "#0a0f0a" }}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-brand-400">Pricing</p>
          <h2 className="text-3xl font-bold text-white sm:text-4xl">Start free. Scale as you grow.</h2>
          <p className="mt-4 text-surface-400">No credit card required for the free plan. 14-day trial on paid plans.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {PLANS.map(({ name, price, note, highlight, features, cta }) => (
            <div
              key={name}
              className={[
                "relative flex flex-col rounded-2xl p-7 transition-all",
                highlight
                  ? "bg-brand-600 ring-2 ring-brand-500 shadow-xl shadow-brand-600/20"
                  : "bg-surface-800/40 border border-white/10 hover:border-white/20",
              ].join(" ")}
            >
              {highlight && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full border border-brand-400/30 bg-brand-500 px-3 py-1 text-xs font-bold text-white">
                  Most popular
                </div>
              )}
              <p className={`mb-2 text-xs font-bold uppercase tracking-widest ${highlight ? "text-brand-100" : "text-surface-400"}`}>
                {name}
              </p>
              <div className="mb-6 flex items-baseline gap-1">
                <span className="text-4xl font-black text-white">{price}</span>
                <span className={`text-sm ${highlight ? "text-brand-100" : "text-surface-400"}`}>{note}</span>
              </div>
              <ul className="mb-8 flex-1 space-y-2.5">
                {features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <CheckCircle2 className={`mt-0.5 h-4 w-4 shrink-0 ${highlight ? "text-brand-100" : "text-brand-500"}`} />
                    <span className={highlight ? "text-white" : "text-surface-300"}>{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                href={cta.href}
                className={[
                  "block rounded-xl py-3 text-center text-sm font-bold transition-colors",
                  highlight
                    ? "bg-white text-brand-700 hover:bg-brand-50"
                    : "bg-surface-700 text-white hover:bg-surface-600",
                ].join(" ")}
              >
                {cta.label}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-8 text-center">
          <Link
            href="/pricing"
            className="inline-flex items-center gap-1.5 text-sm text-surface-400 transition-colors hover:text-white"
          >
            See full pricing including Agency and Enterprise plans
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </p>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// CTA banner
// ─────────────────────────────────────────────────────────────────────────────

function CTABanner() {
  return (
    <section className="relative overflow-hidden bg-brand-600 py-20 sm:py-24">
      {/* Radial glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: "radial-gradient(ellipse 70% 80% at 50% 50%, rgba(255,255,255,0.07), transparent)",
        }}
      />
      {/* Dot pattern */}
      <div
        className="pointer-events-none absolute inset-0 opacity-10"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-sm">
          <Leaf className="h-7 w-7 text-white" />
        </div>
        <h2 className="mb-4 text-4xl font-black text-white sm:text-5xl">
          Your first GHG inventory starts today.
        </h2>
        <p className="mx-auto mb-10 max-w-lg text-lg text-brand-100">
          Free for one entity, one user, one reporting year. No credit card required.
          Upgrade when you&apos;re ready.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-sm font-bold text-brand-700 shadow-lg transition-colors hover:bg-brand-50"
          >
            Start for free — no credit card
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 rounded-xl border border-brand-400/50 px-8 py-4 text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-brand-700"
          >
            Book a demo
          </Link>
        </div>
        <p className="mt-6 text-sm text-brand-200">
          Trusted by sustainability managers, ESG consultants, and development project teams.
        </p>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <>
      <OrganizationJsonLd />
      <NavBar />
      <main>
        <Hero />
        <TrustBar />
        <StatsSection />
        <ProblemSection />
        <HowItWorks />
        <FeaturesSection />
        <ComparisonSection />
        <DataSources />
        <EstimatorSection />
        <SecuritySection />
        <PricingTeaser />
        <CTABanner />
      </main>
      <Footer />
    </>
  );
}

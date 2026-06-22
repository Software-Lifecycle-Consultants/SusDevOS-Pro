import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  BarChart3,
  Leaf,
  Shield,
  BookOpen,
  Database,
  Globe,
} from "lucide-react";
import { NavBar }          from "@/components/marketing/NavBar";
import { Footer }          from "@/components/marketing/Footer";
import { FeatureTabs }     from "@/components/marketing/FeatureTabs";
import { CarbonEstimator } from "@/components/marketing/CarbonEstimator";

export const metadata: Metadata = {
  title: "SusDevOS — GHG Reporting & Ecosystem Tracking for Development Projects",
  description:
    "Calculate your Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate GHG Protocol-conformant reports. Free to start. Built for SBTi, CDP and TNFD.",
  keywords:
    "GHG reporting software, carbon footprint calculator, Scope 3 emissions, SBTi target tracking, TNFD biodiversity, emissions inventory",
  openGraph: {
    title:       "SusDevOS — GHG Reporting & Ecosystem Tracking",
    description: "Calculate Scope 1, 2 and 3 emissions, track biodiversity impacts, and generate audit-ready GHG reports. Free to start.",
    type:        "website",
    url:         "https://susdevos.com",
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Hero
// ─────────────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-brand-50 via-white to-white py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700 mb-6">
              <CheckCircle2 className="h-3.5 w-3.5" />
              GHG Protocol · SBTi · CDP · TNFD aligned
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-surface-900 leading-[1.1] tracking-tight mb-5">
              Your GHG inventory,{" "}
              <span className="text-brand-600">verified and submission-ready</span>
              {" "}— without the spreadsheet hell.
            </h1>
            <p className="text-lg text-surface-500 leading-relaxed mb-8 max-w-lg">
              SusDevOS calculates Scope 1, 2 and 3 emissions, tracks ecosystem impacts,
              and generates audit-ready reports aligned to GHG Protocol, SBTi, CDP and TNFD.
              Free to start.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 bg-brand-600 text-white px-6 py-3 rounded-lg text-sm font-semibold hover:bg-brand-700 transition-colors shadow-sm"
              >
                Start for free
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/demo"
                className="inline-flex items-center gap-2 bg-white text-surface-700 border border-surface-200 px-6 py-3 rounded-lg text-sm font-semibold hover:bg-surface-50 transition-colors shadow-sm"
              >
                Book a demo
              </Link>
            </div>
            <p className="text-xs text-surface-400 mt-3">No credit card required for the free plan.</p>
          </div>

          {/* Dashboard mockup */}
          <div className="hidden lg:block">
            <div className="rounded-2xl border border-surface-200 bg-white shadow-xl overflow-hidden">
              <div className="flex items-center gap-1.5 bg-surface-50 border-b border-surface-200 px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-red-400" />
                <div className="h-3 w-3 rounded-full bg-amber-400" />
                <div className="h-3 w-3 rounded-full bg-green-400" />
                <div className="flex-1 mx-3 bg-surface-100 rounded px-3 py-1 text-xs text-surface-400">
                  app.susdevos.com/emissions
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-surface-400 uppercase tracking-wide">GHG Inventory 2024</p>
                    <p className="text-sm font-semibold text-surface-800 mt-0.5">Acme Property Group</p>
                  </div>
                  <span className="text-xs bg-brand-100 text-brand-700 px-2.5 py-1 rounded-full font-medium">
                    ✓ Verified
                  </span>
                </div>
                {[
                  { label: "Scope 1 — Direct",      value: "847",   pct: 14, color: "bg-brand-500" },
                  { label: "Scope 2 — Electricity",  value: "1,234", pct: 21, color: "bg-brand-400" },
                  { label: "Scope 3 — Value chain",  value: "3,891", pct: 65, color: "bg-brand-300" },
                ].map(({ label, value, pct, color }) => (
                  <div key={label}>
                    <div className="flex justify-between text-xs text-surface-500 mb-1">
                      <span>{label}</span>
                      <span className="font-medium text-surface-700">{value} tCO₂e</span>
                    </div>
                    <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                      <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                ))}
                <div className="border-t border-surface-100 pt-3 flex justify-between items-center">
                  <span className="text-xs text-surface-500">Net total</span>
                  <span className="text-lg font-bold text-surface-900">5,972 tCO₂e</span>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1 rounded-lg bg-brand-50 border border-brand-100 p-3">
                    <p className="text-[10px] text-brand-600 font-medium uppercase tracking-wide">SBTi target</p>
                    <p className="text-xs text-surface-700 mt-0.5 font-medium">On track ↓12% vs 2022</p>
                  </div>
                  <div className="flex-1 rounded-lg bg-surface-50 border border-surface-100 p-3">
                    <p className="text-[10px] text-surface-500 font-medium uppercase tracking-wide">Report ready</p>
                    <p className="text-xs text-surface-700 mt-0.5 font-medium">CDP · PDF · CSV</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Trust bar
// ─────────────────────────────────────────────────────────────────────────────

const STANDARDS = [
  { abbr: "GHG Protocol", note: "All 15 Scope 3 categories"       },
  { abbr: "SBTi",         note: "1.5°C pathway targets"           },
  { abbr: "CDP",          note: "Questionnaire-ready export"      },
  { abbr: "TNFD",         note: "LEAP framework aligned"          },
  { abbr: "IPCC",         note: "AR6 GWP100 & LULUCF biomass"    },
  { abbr: "UN SDGs",      note: "SDG 13, 15, 7 & 11 mapping"     },
];

function TrustBar() {
  return (
    <section className="border-y border-surface-100 bg-white py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="text-center text-xs uppercase tracking-widest text-surface-400 font-medium mb-8">
          Aligned to the standards that matter
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-6">
          {STANDARDS.map(({ abbr, note }) => (
            <div key={abbr} className="text-center">
              <p className="text-sm font-semibold text-surface-700">{abbr}</p>
              <p className="text-xs text-surface-400 mt-0.5 leading-snug">{note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Problem statement
// ─────────────────────────────────────────────────────────────────────────────

const PROBLEMS = [
  {
    icon:  Database,
    title: '"Our data is all over the place."',
    body:  "Activity data in one spreadsheet, emission factors in another, reports emailed as PDFs. One wrong formula breaks the whole inventory.",
  },
  {
    icon:  Shield,
    title: '"We can\'t prove our numbers."',
    body:  "Auditors and verifiers need a full calculation trail. Spreadsheets don't provide one, and recreating the methodology during a review takes weeks.",
  },
  {
    icon:  BookOpen,
    title: '"It takes months every year."',
    body:  "Manual data collection, chasing suppliers for Scope 3 data, formatting reports. The same work, repeated annually, with no institutional memory.",
  },
];

function ProblemSection() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mb-12">
          <h2 className="text-3xl font-bold text-surface-900 mb-4">
            Most sustainability teams are still working in Excel.{" "}
            <span className="text-surface-400">That&apos;s a problem.</span>
          </h2>
        </div>
        <div className="grid gap-6 sm:grid-cols-3">
          {PROBLEMS.map(({ icon: Icon, title, body }) => (
            <div key={title} className="bg-white rounded-xl border border-surface-200 p-6 shadow-sm">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-100 mb-4">
                <Icon className="h-5 w-5 text-surface-600" />
              </div>
              <h3 className="font-semibold text-surface-900 mb-2 leading-snug">{title}</h3>
              <p className="text-sm text-surface-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
        <p className="text-center text-surface-500 mt-10 text-lg font-medium">SusDevOS solves all three.</p>
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
    body:   "Enter fuel consumption, electricity use, business travel, purchased goods — in the units you already have. Emission factors from DEFRA, EPA and the IPCC are applied automatically. No formula required.",
  },
  {
    number: "02",
    title:  "Review your calculated inventory",
    body:   "See your Scope 1, 2 and 3 totals in real time. Both location-based and market-based Scope 2 are calculated simultaneously. Track progress against SBTi targets. Flag data quality issues before they become audit findings.",
  },
  {
    number: "03",
    title:  "Generate and submit your report",
    body:   "One click produces a GHG Protocol-conformant PDF, ready for CDP submission, verifier review, or internal disclosure. The full calculation methodology — every emission factor, every GWP value — is included.",
  },
];

function HowItWorks() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mx-auto text-center mb-14">
          <h2 className="text-3xl font-bold text-surface-900 mb-4">
            From activity data to verified report in three steps
          </h2>
          <p className="text-surface-500">No configuration. No consultant required. Start entering data on day one.</p>
        </div>
        <div className="grid gap-8 sm:grid-cols-3">
          {STEPS.map(({ number, title, body }) => (
            <div key={number}>
              <p className="text-5xl font-bold text-brand-100 mb-4 select-none">{number}</p>
              <h3 className="text-lg font-semibold text-surface-900 mb-2">{title}</h3>
              <p className="text-sm text-surface-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Feature highlights (persona tabs)
// ─────────────────────────────────────────────────────────────────────────────

function FeaturesSection() {
  return (
    <section className="bg-surface-50 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mb-10">
          <h2 className="text-3xl font-bold text-surface-900 mb-4">
            Built for every role in the sustainability team
          </h2>
          <p className="text-surface-500">
            Whether you&apos;re managing one entity or thirty client accounts, SusDevOS fits your workflow.
          </p>
        </div>
        <FeatureTabs />
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Data sources
// ─────────────────────────────────────────────────────────────────────────────

const DATA_SOURCES = [
  { name: "DEFRA",        desc: "UK Government greenhouse gas conversion factors — updated annually"   },
  { name: "EPA eGRID",    desc: "US electricity grid emission rates by subregion"                      },
  { name: "IPCC 2006",    desc: "LULUCF biomass carbon stock tables and growth parameters"             },
  { name: "Climatiq",     desc: "Global emission factor aggregator with 50,000+ factors"              },
  { name: "Verra VCS",    desc: "Voluntary carbon credit registry — retirement validation"             },
  { name: "GBIF / IUCN",  desc: "Biodiversity taxonomy and species conservation status"               },
  { name: "ECB",          desc: "Daily FX rates for spend-based Scope 3 multi-currency conversion"    },
  { name: "SBTi",         desc: "Monthly sync of the SBTi Companies Taking Action registry"           },
];

function DataSources() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mx-auto text-center mb-12">
          <h2 className="text-3xl font-bold text-surface-900 mb-4">Built on authoritative data sources</h2>
          <p className="text-surface-500">
            Your emission factors, offset validations and biodiversity records are sourced from
            the same databases your verifier and regulator use.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {DATA_SOURCES.map(({ name, desc }) => (
            <div key={name} className="rounded-xl border border-surface-200 p-5">
              <p className="font-semibold text-surface-800 text-sm mb-1.5">{name}</p>
              <p className="text-xs text-surface-500 leading-relaxed">{desc}</p>
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

const PLANS_TEASER = [
  {
    name:      "Free",
    price:     "£0",
    note:      "forever",
    highlight: false,
    features:  [
      "1 entity",
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
      "All scopes including Scope 3",
      "All emission factor libraries",
      "Formal GHG inventory + SBTi",
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
      "Verification workflow + CDP",
      "GIS land parcel mapping",
      "IPCC Tier 2/3 biomass",
      "API access · bulk import",
    ],
    cta: { label: "Start 14-day trial", href: "/register?plan=professional" },
  },
];

function PricingTeaser() {
  return (
    <section className="bg-surface-900 py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mx-auto text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">Start free. Scale as you grow.</h2>
          <p className="text-surface-400">No credit card required for the free plan. 14-day trial on paid plans.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {PLANS_TEASER.map(({ name, price, note, highlight, features, cta }) => (
            <div
              key={name}
              className={[
                "rounded-2xl p-6 flex flex-col",
                highlight ? "bg-brand-600 text-white ring-2 ring-brand-400" : "bg-surface-800 text-surface-200",
              ].join(" ")}
            >
              <p className={`text-xs uppercase tracking-wide font-semibold mb-2 ${highlight ? "text-brand-100" : "text-surface-400"}`}>
                {name}
              </p>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-3xl font-bold">{price}</span>
                <span className={`text-sm ${highlight ? "text-brand-100" : "text-surface-400"}`}>{note}</span>
              </div>
              <ul className="space-y-2 mb-6 flex-1">
                {features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className={`h-4 w-4 mt-0.5 shrink-0 ${highlight ? "text-brand-100" : "text-brand-400"}`} />
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href={cta.href}
                className={[
                  "text-sm font-semibold text-center py-2.5 rounded-lg transition-colors",
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
        <p className="text-center mt-8">
          <Link href="/pricing" className="text-sm text-surface-400 hover:text-white transition-colors inline-flex items-center gap-1">
            See full pricing including Agency and Enterprise plans
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </p>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Carbon estimator section
// ─────────────────────────────────────────────────────────────────────────────

function EstimatorSection() {
  return (
    <section className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl mx-auto text-center mb-12">
          <h2 className="text-3xl font-bold text-surface-900 mb-4">
            How big is your carbon footprint?
          </h2>
          <p className="text-surface-500">Find out in 60 seconds. Three questions — we do the maths.</p>
        </div>
        <CarbonEstimator />
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Final CTA banner
// ─────────────────────────────────────────────────────────────────────────────

function CTABanner() {
  return (
    <section className="bg-brand-600 py-16">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <Globe className="h-10 w-10 text-brand-200 mx-auto mb-4" />
        <h2 className="text-3xl font-bold text-white mb-4">Your first GHG inventory starts today.</h2>
        <p className="text-brand-100 mb-8 max-w-lg mx-auto">
          Free for one entity, one user, one reporting year. No credit card required. Upgrade when you&apos;re ready.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="bg-white text-brand-700 px-6 py-3 rounded-lg text-sm font-semibold hover:bg-brand-50 transition-colors shadow-sm inline-flex items-center gap-2"
          >
            Start for free — no credit card
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="border border-brand-400 text-white px-6 py-3 rounded-lg text-sm font-semibold hover:bg-brand-700 transition-colors"
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

export default function HomePage() {
  return (
    <>
      <NavBar />
      <main>
        <Hero />
        <TrustBar />
        <ProblemSection />
        <HowItWorks />
        <FeaturesSection />
        <DataSources />
        <PricingTeaser />
        <EstimatorSection />
        <CTABanner />
      </main>
      <Footer />
    </>
  );
}

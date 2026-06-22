"use client";

import type { Metadata } from "next";
import Link from "next/link";
import { useState } from "react";
import { CheckCircle2, Minus, ArrowRight } from "lucide-react";

// Metadata can't be exported from a "use client" file in Next 14 App Router.
// Move to a server wrapper if SSR meta is needed.

const PLANS = [
  {
    id:          "free",
    name:        "Free",
    monthly:     0,
    annual:      0,
    note:        "Forever free",
    highlight:   false,
    cta:         { label: "Start for free",        href: "/register"                    },
    description: "For a single company doing their first GHG inventory.",
    limits:      "1 entity · 1 user · current year only",
  },
  {
    id:          "starter",
    name:        "Starter",
    monthly:     49,
    annual:      39,
    note:        "Save 20% annually",
    highlight:   false,
    cta:         { label: "Start 14-day trial",    href: "/register?plan=starter"       },
    description: "For SMEs that need a full annual Scope 1/2/3 inventory.",
    limits:      "1 entity · 5 users · 3 reporting years",
  },
  {
    id:          "professional",
    name:        "Professional",
    monthly:     199,
    annual:      159,
    note:        "Save 20% annually",
    highlight:   true,
    cta:         { label: "Start 14-day trial",    href: "/register?plan=professional"  },
    description: "For organisations with subsidiaries or that need verification workflows.",
    limits:      "5 entities · 20 users · unlimited years",
  },
  {
    id:          "agency",
    name:        "Agency",
    monthly:     499,
    annual:      399,
    note:        "Save 20% annually",
    highlight:   false,
    cta:         { label: "Start 14-day trial",    href: "/register?plan=agency"        },
    description: "For sustainability consultancies managing multiple client inventories.",
    limits:      "25 entities · unlimited users",
  },
  {
    id:          "enterprise",
    name:        "Enterprise",
    monthly:     null,
    annual:      null,
    note:        "Custom annual contract",
    highlight:   false,
    cta:         { label: "Talk to sales",         href: "/contact?subject=enterprise"  },
    description: "For large corporates, government, or organisations needing SSO/data residency.",
    limits:      "Unlimited entities · unlimited users",
  },
] as const;

type PlanId = typeof PLANS[number]["id"];

const FEATURE_GROUPS: {
  group: string;
  rows: { label: string; tip?: string; plans: Record<PlanId, string | boolean | null> }[];
}[] = [
  {
    group: "Entities & users",
    rows: [
      { label: "Entities",          plans: { free: "1", starter: "1", professional: "5", agency: "25", enterprise: "Unlimited" } },
      { label: "Users per entity",  plans: { free: "1", starter: "5", professional: "20", agency: "Unlimited", enterprise: "Unlimited" } },
      { label: "Reporting years",   plans: { free: "1 (current)", starter: "3", professional: "Unlimited", agency: "Unlimited", enterprise: "Unlimited" } },
    ],
  },
  {
    group: "GHG calculations",
    rows: [
      { label: "Scope 1",                                  plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 2 (location-based)",                 plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 2 (market-based)",                   plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 3 (all 15 categories)",              plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "GWP dataset selection (AR4/AR5/AR6)",      plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "DEFRA emission factors",                   plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Climatiq / EPA eGRID emission factors",    plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Formal GHG inventory (versioned)",         plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Bulk CSV import",                          plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Targets & offsets",
    rows: [
      { label: "SBTi target setting & milestones",     plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "SBTi registry sync (monthly)",         plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Carbon offset management",             plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Verra / Gold Standard validation",     plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Ecosystem & land",
    rows: [
      { label: "Ecosystem tracking (basic)",           plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "GIS land parcel mapping",              plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "IPCC biomass (Tier 1)",                plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "IPCC biomass (Tier 2/3)",              plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Restoration sequestration",            plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "TNFD-aligned reporting",               plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Verification & reporting",
    rows: [
      { label: "Internal approval workflow",           plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Third-party verification support",     plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "PDF report (watermarked)",             plans: { free: true, starter: false, professional: false, agency: false, enterprise: false } },
      { label: "PDF report (unbranded)",               plans: { free: false, starter: true, professional: true, agency: false, enterprise: false } },
      { label: "PDF report (white-label)",             plans: { free: false, starter: false, professional: false, agency: true, enterprise: true } },
      { label: "CSV / JSON export",                    plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "CDP export format",                    plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Client read-only portal",              plans: { free: false, starter: false, professional: false, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Admin & security",
    rows: [
      { label: "Audit log (30 days)",   plans: { free: true, starter: true, professional: false, agency: false, enterprise: false } },
      { label: "Audit log (1 year)",    plans: { free: false, starter: false, professional: true, agency: true, enterprise: false } },
      { label: "Audit log (7 years)",   plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
      { label: "User privilege overrides", plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Entity API keys",       plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "SSO / SAML",           plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
      { label: "Dedicated instance",   plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
    ],
  },
  {
    group: "Support",
    rows: [
      { label: "Support",              plans: { free: "Docs only", starter: "Email (48 h)", professional: "Email (24 h)", agency: "Priority (8 h)", enterprise: "Dedicated CSM" } },
      { label: "SLA",                  plans: { free: null, starter: null, professional: null, agency: "99.5%", enterprise: "99.9%" } },
    ],
  },
];

const FAQ = [
  {
    q: "What counts as an entity?",
    a: "A legal entity: a company, subsidiary, or branch with its own GHG inventory boundary. Most companies need just one. Subsidiaries with separate reporting obligations each need their own entity record.",
  },
  {
    q: "Can I switch plans?",
    a: "Yes. Upgrades take effect immediately. Downgrades take effect at the next billing date. Your data is always retained.",
  },
  {
    q: "Is there a free trial for paid plans?",
    a: "14-day trial on Starter and Professional — no credit card required. If you don't add a card before the trial ends, your account reverts to Free. Data is never deleted during a trial.",
  },
  {
    q: "Do you offer discounts for NGOs or academia?",
    a: "Yes — registered charities, NGOs and academic institutions qualify for a 50% discount. Contact us with proof of status. Government entities use Enterprise pricing.",
  },
  {
    q: "What happens to my data if I cancel?",
    a: "Data is retained for 90 days after cancellation, during which you can export everything. After 90 days you'll receive a final warning before permanent deletion. You can always reactivate within that window.",
  },
  {
    q: "Is VAT included?",
    a: "Prices are shown ex-VAT. UK VAT (20%) is added at checkout for UK customers. EU customers are charged at the rate applicable in their member state.",
  },
];

function CellValue({ val }: { val: string | boolean | null }) {
  if (val === true)  return <CheckCircle2 className="h-5 w-5 text-brand-500 mx-auto" />;
  if (val === false) return <Minus className="h-4 w-4 text-surface-300 mx-auto" />;
  if (val === null)  return <Minus className="h-4 w-4 text-surface-300 mx-auto" />;
  return <span className="text-xs text-surface-600 text-center block">{val}</span>;
}

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);

  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="bg-gradient-to-b from-surface-50 to-white py-16 sm:py-20 border-b border-surface-100">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 text-center">
          <h1 className="text-4xl font-bold text-surface-900 mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-surface-500 text-lg max-w-xl mx-auto mb-8">
            Free for one entity. Starter from £49/month. No hidden fees, no per-seat surprises.
          </p>

          {/* Monthly / Annual toggle */}
          <div className="inline-flex items-center gap-3 bg-surface-100 rounded-full px-4 py-2">
            <button
              onClick={() => setAnnual(false)}
              className={`text-sm font-medium px-3 py-1.5 rounded-full transition-colors ${!annual ? "bg-white text-surface-900 shadow-sm" : "text-surface-500 hover:text-surface-700"}`}
            >
              Monthly
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`text-sm font-medium px-3 py-1.5 rounded-full transition-colors ${annual ? "bg-white text-surface-900 shadow-sm" : "text-surface-500 hover:text-surface-700"}`}
            >
              Annual
              <span className="ml-1.5 text-xs text-brand-600 font-semibold">−20%</span>
            </button>
          </div>
        </div>
      </section>

      {/* Plan cards */}
      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {PLANS.map(({ id, name, monthly, annual: annualPrice, note, highlight, cta, description, limits }) => {
              const price    = annual ? annualPrice : monthly;
              const showNote = annual && annualPrice !== null;

              return (
                <div
                  key={id}
                  className={[
                    "rounded-2xl border p-5 flex flex-col",
                    highlight
                      ? "border-brand-400 bg-brand-50 ring-2 ring-brand-400"
                      : "border-surface-200 bg-white",
                  ].join(" ")}
                >
                  {highlight && (
                    <p className="text-xs font-semibold text-brand-600 uppercase tracking-wide mb-2">
                      Most popular
                    </p>
                  )}
                  <p className="font-bold text-surface-900 mb-1">{name}</p>
                  <p className="text-xs text-surface-500 leading-snug mb-4">{description}</p>

                  {price !== null ? (
                    <div className="mb-1">
                      <span className="text-2xl font-bold text-surface-900">£{price}</span>
                      <span className="text-sm text-surface-400"> /mo</span>
                    </div>
                  ) : (
                    <div className="mb-1">
                      <span className="text-xl font-bold text-surface-900">Custom</span>
                    </div>
                  )}
                  {showNote && price !== null && (
                    <p className="text-xs text-brand-600 font-medium mb-3">{note}</p>
                  )}
                  {!showNote && <p className="text-xs text-surface-400 mb-3">{note}</p>}

                  <p className="text-[11px] text-surface-400 mb-5 leading-snug">{limits}</p>

                  <Link
                    href={cta.href}
                    className={[
                      "mt-auto text-sm font-semibold text-center py-2.5 rounded-lg transition-colors",
                      highlight
                        ? "bg-brand-600 text-white hover:bg-brand-700"
                        : "bg-surface-100 text-surface-800 hover:bg-surface-200",
                    ].join(" ")}
                  >
                    {cta.label}
                  </Link>
                </div>
              );
            })}
          </div>

          <p className="text-center text-xs text-surface-400 mt-4">
            Entity add-ons: +£25/entity/month (Professional) · +£15/entity/month (Agency)
          </p>
        </div>
      </section>

      {/* Feature comparison table */}
      <section className="py-12 sm:py-16 border-t border-surface-100">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-surface-900 mb-8 text-center">Full feature comparison</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[700px]">
              <thead>
                <tr className="border-b border-surface-200">
                  <th className="text-left py-3 pr-4 font-medium text-surface-500 w-48">Feature</th>
                  {PLANS.map(({ id, name, highlight }) => (
                    <th
                      key={id}
                      className={`text-center py-3 px-3 font-semibold ${highlight ? "text-brand-700" : "text-surface-700"}`}
                    >
                      {name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FEATURE_GROUPS.map(({ group, rows }) => (
                  <>
                    <tr key={group} className="bg-surface-50">
                      <td
                        colSpan={6}
                        className="py-2 px-0 text-xs uppercase tracking-wider font-semibold text-surface-500 pt-5"
                      >
                        {group}
                      </td>
                    </tr>
                    {rows.map(({ label, plans }) => (
                      <tr key={label} className="border-b border-surface-100 hover:bg-surface-50">
                        <td className="py-2.5 pr-4 text-surface-600">{label}</td>
                        {PLANS.map(({ id }) => (
                          <td key={id} className="py-2.5 px-3 text-center">
                            <CellValue val={plans[id]} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 sm:py-20 border-t border-surface-100 bg-surface-50">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <h2 className="text-2xl font-bold text-surface-900 mb-10 text-center">Frequently asked questions</h2>
          <div className="space-y-6">
            {FAQ.map(({ q, a }) => (
              <div key={q}>
                <h3 className="font-semibold text-surface-900 mb-2">{q}</h3>
                <p className="text-surface-500 text-sm leading-relaxed">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise CTA */}
      <section className="py-16 border-t border-surface-100 bg-white">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center">
          <h2 className="text-2xl font-bold text-surface-900 mb-3">
            More than 25 entities, or need a dedicated instance?
          </h2>
          <p className="text-surface-500 mb-6">
            Enterprise contracts include unlimited entities, SSO/SAML, custom data residency,
            a dedicated CSM, and a 99.9% SLA. Minimum £24,000/year.
          </p>
          <Link
            href="/contact?subject=enterprise"
            className="inline-flex items-center gap-2 bg-surface-900 text-white px-6 py-3 rounded-lg text-sm font-semibold hover:bg-surface-800 transition-colors"
          >
            Talk to sales
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}

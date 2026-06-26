"use client";

import Link from "next/link";
import { useState } from "react";
import { CheckCircle2, Minus, ArrowRight } from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// Currency
// ─────────────────────────────────────────────────────────────────────────────

type CurrencyCode = "GBP" | "EUR" | "USD" | "AUD";

const CURRENCIES: { code: CurrencyCode; symbol: string; label: string; flag: string }[] = [
  { code: "GBP", symbol: "£",  label: "GBP", flag: "🇬🇧" },
  { code: "EUR", symbol: "€",  label: "EUR", flag: "🇪🇺" },
  { code: "USD", symbol: "$",  label: "USD", flag: "🇺🇸" },
  { code: "AUD", symbol: "A$", label: "AUD", flag: "🇦🇺" },
];

// [monthly, annual] per plan. null = custom/contact.
const PRICES: Record<CurrencyCode, Record<string, [number | null, number | null]>> = {
  GBP: { free: [0, 0],   starter: [49,  39],  professional: [199,  159],  agency: [499,  399],  enterprise: [null, null] },
  EUR: { free: [0, 0],   starter: [59,  47],  professional: [239,  189],  agency: [599,  479],  enterprise: [null, null] },
  USD: { free: [0, 0],   starter: [59,  47],  professional: [249,  199],  agency: [629,  499],  enterprise: [null, null] },
  AUD: { free: [0, 0],   starter: [89,  69],  professional: [379,  299],  agency: [949,  749],  enterprise: [null, null] },
};

// Entity add-on [professional, agency] per currency
const ADDONS: Record<CurrencyCode, [number, number]> = {
  GBP: [25, 15],
  EUR: [29, 18],
  USD: [29, 19],
  AUD: [45, 27],
};

// Tax notes per currency shown under price cards
const TAX_NOTES: Record<CurrencyCode, string> = {
  GBP: "Prices ex-VAT. UK VAT (20%) added at checkout.",
  EUR: "Prices ex-VAT. Local EU VAT rate applied at checkout.",
  USD: "Prices exclusive of applicable state/local taxes.",
  AUD: "Prices ex-GST. Australian GST (10%) added at checkout.",
};

// ─────────────────────────────────────────────────────────────────────────────
// Plans
// ─────────────────────────────────────────────────────────────────────────────

const PLANS = [
  {
    id:          "free",
    name:        "Free",
    note:        "Forever free",
    highlight:   false,
    cta:         { label: "Start for free",     href: "/register"                   },
    description: "For a single company doing their first GHG inventory.",
    limits:      "1 entity · 1 user · current year only",
  },
  {
    id:          "starter",
    name:        "Starter",
    note:        "Save 20% annually",
    highlight:   false,
    cta:         { label: "Start 14-day trial", href: "/register?plan=starter"      },
    description: "For SMEs that need a full annual Scope 1/2/3 inventory.",
    limits:      "1 entity · 5 users · 3 reporting years",
  },
  {
    id:          "professional",
    name:        "Professional",
    note:        "Save 20% annually",
    highlight:   true,
    cta:         { label: "Start 14-day trial", href: "/register?plan=professional" },
    description: "For organisations with subsidiaries or that need verification workflows.",
    limits:      "5 entities · 20 users · unlimited years",
  },
  {
    id:          "agency",
    name:        "Agency",
    note:        "Save 20% annually",
    highlight:   false,
    cta:         { label: "Start 14-day trial", href: "/register?plan=agency"       },
    description: "For sustainability consultancies managing multiple client inventories.",
    limits:      "25 entities · unlimited users",
  },
  {
    id:          "enterprise",
    name:        "Enterprise",
    note:        "Custom annual contract",
    highlight:   false,
    cta:         { label: "Talk to sales",      href: "/contact?subject=enterprise" },
    description: "For large corporates, government, or organisations needing SSO/data residency.",
    limits:      "Unlimited entities · unlimited users",
  },
] as const;

type PlanId = typeof PLANS[number]["id"];

// ─────────────────────────────────────────────────────────────────────────────
// Feature comparison
// ─────────────────────────────────────────────────────────────────────────────

const FEATURE_GROUPS: {
  group: string;
  rows: { label: string; plans: Record<PlanId, string | boolean | null> }[];
}[] = [
  {
    group: "Entities & users",
    rows: [
      { label: "Entities",         plans: { free: "1", starter: "1", professional: "5", agency: "25", enterprise: "Unlimited" } },
      { label: "Users per entity", plans: { free: "1", starter: "5", professional: "20", agency: "Unlimited", enterprise: "Unlimited" } },
      { label: "Reporting years",  plans: { free: "1 (current)", starter: "3", professional: "Unlimited", agency: "Unlimited", enterprise: "Unlimited" } },
    ],
  },
  {
    group: "GHG calculations",
    rows: [
      { label: "Scope 1",                               plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 2 (location-based)",              plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 2 (market-based)",                plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Scope 3 (all 15 categories)",           plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "GWP dataset selection (AR4/AR5/AR6)",   plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "DEFRA emission factors",                plans: { free: true, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Climatiq / EPA eGRID factors",          plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Formal GHG inventory (versioned)",      plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Bulk CSV import",                       plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Targets & offsets",
    rows: [
      { label: "Carbon goals & target milestones",  plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Carbon offset management",          plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Verra / Gold Standard validation",  plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Ecosystem, land & TNFD",
    rows: [
      { label: "Ecosystem tracking (basic)",      plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "GIS land parcel mapping",         plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "IPCC biomass (Tier 1)",           plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "IPCC biomass (Tier 2/3)",         plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Restoration sequestration",       plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "TNFD LEAP reporting",             plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Species / IUCN tracking",         plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Verification & reporting",
    rows: [
      { label: "Internal approval workflow",      plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Third-party verification support",plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "PDF report (watermarked)",        plans: { free: true, starter: false, professional: false, agency: false, enterprise: false } },
      { label: "PDF report (unbranded)",          plans: { free: false, starter: true, professional: true, agency: false, enterprise: false } },
      { label: "PDF report (white-label)",        plans: { free: false, starter: false, professional: false, agency: true, enterprise: true } },
      { label: "CSV / JSON export",               plans: { free: false, starter: true, professional: true, agency: true, enterprise: true } },
      { label: "Client read-only portal",         plans: { free: false, starter: false, professional: false, agency: true, enterprise: true } },
    ],
  },
  {
    group: "Admin & security",
    rows: [
      { label: "Audit log (30 days)",          plans: { free: true, starter: true, professional: false, agency: false, enterprise: false } },
      { label: "Audit log (1 year)",           plans: { free: false, starter: false, professional: true, agency: true, enterprise: false } },
      { label: "Audit log (7 years)",          plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
      { label: "User privilege overrides",     plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "Entity API keys",              plans: { free: false, starter: false, professional: true, agency: true, enterprise: true } },
      { label: "SSO / SAML",                  plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
      { label: "Dedicated instance",           plans: { free: false, starter: false, professional: false, agency: false, enterprise: true } },
    ],
  },
  {
    group: "Support",
    rows: [
      { label: "Support", plans: { free: "Docs only", starter: "Email (48 h)", professional: "Email (24 h)", agency: "Priority (8 h)", enterprise: "Dedicated CSM" } },
      { label: "SLA",     plans: { free: null, starter: null, professional: null, agency: "99.5%", enterprise: "99.9%" } },
    ],
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// FAQ
// ─────────────────────────────────────────────────────────────────────────────

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
    q: "Which currencies do you accept?",
    a: "GBP, EUR, USD and AUD. Select your preferred currency above. Prices shown are indicative and reflect approximate exchange rates — your card will be charged in the currency displayed. Enterprise contracts can be invoiced in any of these currencies.",
  },
  {
    q: "Is tax included in the prices shown?",
    a: "No — all prices are shown excluding tax. UK customers are charged VAT at 20%. EU customers are charged at their member state's applicable VAT rate. US customers may be subject to state/local sales tax. Australian customers are charged GST at 10%.",
  },
  {
    q: "Do you offer discounts for NGOs or academia?",
    a: "Yes — registered charities, NGOs and academic institutions qualify for a 50% discount on any paid plan. Contact us with proof of status. Government entities use Enterprise pricing.",
  },
  {
    q: "What happens to my data if I cancel?",
    a: "Data is retained for 90 days after cancellation, during which you can export everything in CSV or JSON. After 90 days you'll receive a final warning before permanent deletion.",
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Components
// ─────────────────────────────────────────────────────────────────────────────

function CellValue({ val }: { val: string | boolean | null }) {
  if (val === true)  return <CheckCircle2 className="mx-auto h-5 w-5 text-brand-500" />;
  if (val === false) return <Minus className="mx-auto h-4 w-4 text-surface-300" />;
  if (val === null)  return <Minus className="mx-auto h-4 w-4 text-surface-300" />;
  return <span className="block text-center text-xs text-surface-600">{val}</span>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function PricingPage() {
  const [annual,   setAnnual]   = useState(false);
  const [currency, setCurrency] = useState<CurrencyCode>("GBP");

  const cur  = CURRENCIES.find((c) => c.code === currency)!;
  const sym  = cur.symbol;
  const [proAddon, agencyAddon] = ADDONS[currency];

  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="border-b border-surface-100 bg-gradient-to-b from-surface-50 to-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 text-center">
          <h1 className="mb-4 text-4xl font-bold text-surface-900">
            Simple, transparent pricing
          </h1>
          <p className="mx-auto mb-8 max-w-xl text-lg text-surface-500">
            Free for one entity. Paid plans from{" "}
            {sym}{PRICES[currency].starter[0]}/month.
            No hidden fees, no per-seat surprises.
          </p>

          {/* Controls: monthly/annual toggle + currency switcher */}
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            {/* Billing toggle */}
            <div className="inline-flex items-center gap-3 rounded-full bg-surface-100 px-4 py-2">
              <button
                onClick={() => setAnnual(false)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  !annual ? "bg-white text-surface-900 shadow-sm" : "text-surface-500 hover:text-surface-700"
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setAnnual(true)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                  annual ? "bg-white text-surface-900 shadow-sm" : "text-surface-500 hover:text-surface-700"
                }`}
              >
                Annual
                <span className="ml-1.5 text-xs font-semibold text-brand-600">−20%</span>
              </button>
            </div>

            {/* Currency switcher */}
            <div className="inline-flex items-center gap-1 rounded-full border border-surface-200 bg-white px-2 py-1.5">
              {CURRENCIES.map(({ code, symbol, label, flag }) => (
                <button
                  key={code}
                  onClick={() => setCurrency(code)}
                  className={[
                    "rounded-full px-3 py-1 text-sm font-medium transition-all",
                    currency === code
                      ? "bg-surface-900 text-white shadow-sm"
                      : "text-surface-500 hover:text-surface-800",
                  ].join(" ")}
                >
                  {flag} {symbol} {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Plan cards */}
      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {PLANS.map(({ id, name, note, highlight, cta, description, limits }) => {
              const [monthly, annualPrice] = PRICES[currency][id];
              const price = annual ? annualPrice : monthly;

              return (
                <div
                  key={id}
                  className={[
                    "flex flex-col rounded-2xl border p-5",
                    highlight
                      ? "border-brand-400 bg-brand-50 ring-2 ring-brand-400"
                      : "border-surface-200 bg-white",
                  ].join(" ")}
                >
                  {highlight && (
                    <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-600">
                      Most popular
                    </p>
                  )}
                  <p className="mb-1 font-bold text-surface-900">{name}</p>
                  <p className="mb-4 text-xs leading-snug text-surface-500">{description}</p>

                  {price !== null ? (
                    <div className="mb-1">
                      <span className="text-2xl font-bold text-surface-900">{sym}{price}</span>
                      <span className="text-sm text-surface-400"> /mo</span>
                    </div>
                  ) : (
                    <div className="mb-1">
                      <span className="text-xl font-bold text-surface-900">Custom</span>
                    </div>
                  )}

                  {annual && price !== null && annualPrice !== null && (
                    <p className="mb-3 text-xs font-medium text-brand-600">{note}</p>
                  )}
                  {!(annual && price !== null && annualPrice !== null) && (
                    <p className="mb-3 text-xs text-surface-400">{note}</p>
                  )}

                  <p className="mb-5 text-[11px] leading-snug text-surface-400">{limits}</p>

                  <Link
                    href={cta.href}
                    className={[
                      "mt-auto rounded-lg py-2.5 text-center text-sm font-semibold transition-colors",
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

          {/* Add-ons + tax note */}
          <div className="mt-4 flex flex-col items-center gap-1 text-center">
            <p className="text-xs text-surface-400">
              Entity add-ons: +{sym}{proAddon}/entity/month (Professional) · +{sym}{agencyAddon}/entity/month (Agency)
            </p>
            <p className="text-xs text-surface-400">{TAX_NOTES[currency]}</p>
            <p className="text-[11px] text-surface-300 mt-0.5">
              Prices are indicative. You will be charged in {currency} at the rate displayed.
            </p>
          </div>
        </div>
      </section>

      {/* Feature comparison */}
      <section className="border-t border-surface-100 py-12 sm:py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="mb-8 text-center text-2xl font-bold text-surface-900">
            Full feature comparison
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-sm">
              <thead>
                <tr className="border-b border-surface-200">
                  <th className="w-48 py-3 pr-4 text-left font-medium text-surface-500">Feature</th>
                  {PLANS.map(({ id, name, highlight }) => (
                    <th
                      key={id}
                      className={`px-3 py-3 text-center font-semibold ${
                        highlight ? "text-brand-700" : "text-surface-700"
                      }`}
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
                      <td colSpan={6} className="py-2 pt-5 text-xs font-semibold uppercase tracking-wider text-surface-500">
                        {group}
                      </td>
                    </tr>
                    {rows.map(({ label, plans }) => (
                      <tr key={label} className="border-b border-surface-100 hover:bg-surface-50">
                        <td className="py-2.5 pr-4 text-surface-600">{label}</td>
                        {PLANS.map(({ id }) => (
                          <td key={id} className="px-3 py-2.5 text-center">
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
      <section className="border-t border-surface-100 bg-surface-50 py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <h2 className="mb-10 text-center text-2xl font-bold text-surface-900">
            Frequently asked questions
          </h2>
          <div className="space-y-6">
            {FAQ.map(({ q, a }) => (
              <div key={q}>
                <h3 className="mb-2 font-semibold text-surface-900">{q}</h3>
                <p className="text-sm leading-relaxed text-surface-500">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise CTA */}
      <section className="border-t border-surface-100 bg-white py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center">
          <h2 className="mb-3 text-2xl font-bold text-surface-900">
            More than 25 entities, or need a dedicated instance?
          </h2>
          <p className="mb-6 text-surface-500">
            Enterprise contracts include unlimited entities, SSO/SAML, custom data residency,
            a dedicated CSM, and a 99.9% SLA. Invoiced in GBP, EUR, USD or AUD.
            Minimum {sym === "£" ? "£" : sym === "€" ? "€" : sym === "$" && currency === "USD" ? "$" : "A$"}
            {currency === "GBP" ? "24,000" : currency === "EUR" ? "29,000" : currency === "USD" ? "30,000" : "45,000"}
            /year.
          </p>
          <Link
            href="/contact?subject=enterprise"
            className="inline-flex items-center gap-2 rounded-lg bg-surface-900 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-surface-800"
          >
            Talk to sales
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}

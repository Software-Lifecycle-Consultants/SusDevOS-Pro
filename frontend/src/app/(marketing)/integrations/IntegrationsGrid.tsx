"use client";

import { useState } from "react";
import { Zap, RefreshCw } from "lucide-react";

type Pattern = "on-demand" | "scheduled" | "both";

interface Integration {
  id:          string;
  name:        string;
  fullName:    string;
  category:    string;
  pattern:     Pattern;
  cadence:     string;
  dot:         string;
  description: string;
  enables:     string;
  tag:         string;
  stat:        string;
}

const INTEGRATIONS: Integration[] = [
  // ── Emission Factors ─────────────────────────────────────────────────────
  {
    id:          "defra",
    name:        "DEFRA",
    fullName:    "UK Government Conversion Factors",
    category:    "Emission Factors",
    pattern:     "scheduled",
    cadence:     "Annual — April",
    dot:         "bg-blue-600",
    description: "The standard UK emission factor dataset, published by the Department for Energy Security and Net Zero each March. Covers fuel combustion, electricity, refrigerants, transport, and waste across all Scope 1, 2 and 3 categories.",
    enables:     "Scope 1, 2 and 3 emission factors for UK entities",
    tag:         "Public dataset",
    stat:        "600+ factors",
  },
  {
    id:          "epa-egrid",
    name:        "EPA eGRID",
    fullName:    "US Electricity Grid Emission Rates",
    category:    "Emission Factors",
    pattern:     "scheduled",
    cadence:     "Annual — January",
    dot:         "bg-indigo-600",
    description: "US electricity grid emission rates by eGRID subregion (ERCOT, WECC, NPCC and 23 others). Required for location-based Scope 2 calculations for any US facility. Auto-mapped from state to subregion.",
    enables:     "Location-based Scope 2 for US facilities",
    tag:         "Public dataset",
    stat:        "26 subregions",
  },
  {
    id:          "climatiq",
    name:        "Climatiq",
    fullName:    "Global Emission Factor Aggregator",
    category:    "Emission Factors",
    pattern:     "both",
    cadence:     "On-demand + weekly sync",
    dot:         "bg-teal-600",
    description: "A unified emission factor API aggregating DEFRA, EPA, IPCC, EXIOBASE and more into a single interface. Used as the fallback when no local factor exists for a given activity type and region — the result is then cached locally.",
    enables:     "Fallback EF lookup for any activity in any region",
    tag:         "Paid API",
    stat:        "50,000+ factors",
  },
  {
    id:          "iea",
    name:        "IEA",
    fullName:    "International Energy Agency",
    category:    "Emission Factors",
    pattern:     "scheduled",
    cadence:     "Annual",
    dot:         "bg-violet-600",
    description: "International electricity grid emission intensities for countries outside the UK and US. Enables location-based Scope 2 calculations for global operations with country-specific grid data.",
    enables:     "Location-based Scope 2 for non-UK/US operations",
    tag:         "Public dataset",
    stat:        "130+ countries",
  },

  // ── Registries & Standards ───────────────────────────────────────────────
  {
    id:          "verra",
    name:        "Verra VCS",
    fullName:    "Verified Carbon Standard Registry",
    category:    "Registries & Standards",
    pattern:     "both",
    cadence:     "On-demand + daily cache",
    dot:         "bg-emerald-700",
    description: "The world's largest voluntary carbon credit registry. When you log a carbon offset with a VCS serial number, SusDevOS validates it in real time — confirming the credit exists, is not double-retired, and is retired in your entity's name.",
    enables:     "Real-time VCS credit validation against the registry",
    tag:         "Registry",
    stat:        "2,000+ projects",
  },
  {
    id:          "gold-standard",
    name:        "Gold Standard",
    fullName:    "Gold Standard Foundation Registry",
    category:    "Registries & Standards",
    pattern:     "both",
    cadence:     "On-demand + daily cache",
    dot:         "bg-amber-600",
    description: "Gold Standard project and credit registry validation. Credits are verified by project ID and vintage year. Unvalidated credits are never deducted from your net GHG inventory total until validation passes.",
    enables:     "Gold Standard credit validation and project verification",
    tag:         "Registry",
    stat:        "1,500+ projects",
  },
  // ── Biodiversity ─────────────────────────────────────────────────────────
  {
    id:          "gbif",
    name:        "GBIF",
    fullName:    "Global Biodiversity Information Facility",
    category:    "Biodiversity",
    pattern:     "on-demand",
    cadence:     "On-demand",
    dot:         "bg-lime-600",
    description: "When you enter a tree species by common name, GBIF resolves the accepted scientific name, family, kingdom, and full taxonomy. This enables accurate IPCC Tier 2/3 biomass parameter lookup for carbon stock calculations.",
    enables:     "Scientific name resolution for species records",
    tag:         "Public API",
    stat:        "2B+ occurrence records",
  },
  {
    id:          "iucn",
    name:        "IUCN Red List",
    fullName:    "International Union for Conservation of Nature",
    category:    "Biodiversity",
    pattern:     "on-demand",
    cadence:     "On-demand",
    dot:         "bg-orange-600",
    description: "Fetches the IUCN conservation category (LC, NT, VU, EN, CR, EW, EX) for each species in your ecosystem records. Required for TNFD LEAP framework biodiversity impact assessments.",
    enables:     "Conservation status for TNFD biodiversity reporting",
    tag:         "Paid API",
    stat:        "150,000+ assessed species",
  },

  // ── Company Data ─────────────────────────────────────────────────────────
  {
    id:          "companies-house",
    name:        "Companies House",
    fullName:    "UK Companies House",
    category:    "Company Data",
    pattern:     "on-demand",
    cadence:     "On-demand",
    dot:         "bg-sky-600",
    description: "Auto-populates UK entity records from Companies House. Enter a company registration number and SusDevOS retrieves the registered name, address, SIC codes, incorporation date, and significant control persons — no manual entry.",
    enables:     "UK entity auto-population from registration number",
    tag:         "Public API",
    stat:        "5M+ UK companies",
  },
  {
    id:          "opencorporates",
    name:        "OpenCorporates",
    fullName:    "OpenCorporates Global Registry",
    category:    "Company Data",
    pattern:     "on-demand",
    cadence:     "On-demand",
    dot:         "bg-slate-600",
    description: "Non-UK entity auto-population. When a company is registered outside the UK, OpenCorporates provides the same registration-number-to-entity-data lookup from the local jurisdiction's registry.",
    enables:     "Entity auto-population for non-UK registered companies",
    tag:         "Paid API",
    stat:        "200+ jurisdictions",
  },

  // ── Financial ────────────────────────────────────────────────────────────
  {
    id:          "ecb-oxr",
    name:        "ECB + Open Exchange Rates",
    fullName:    "European Central Bank / Open Exchange Rates",
    category:    "Financial",
    pattern:     "scheduled",
    cadence:     "Daily — 18:00 UTC",
    dot:         "bg-yellow-500",
    description: "Daily FX rate sync from the ECB (primary) with Open Exchange Rates as a failsafe fallback. Applied automatically to spend-based Scope 3 activity data entered in non-USD currencies — spend-based emission factors are USD-denominated.",
    enables:     "Multi-currency Scope 3 spend-based emission calculations",
    tag:         "Public + Paid API",
    stat:        "170+ currency pairs",
  },
];

const CATEGORIES = [
  "All",
  "Emission Factors",
  "Registries & Standards",
  "Biodiversity",
  "Company Data",
  "Financial",
];

const PATTERN_META: Record<Pattern, { label: string; Icon: React.ElementType; cls: string }> = {
  "on-demand": { label: "On-demand",          Icon: Zap,       cls: "bg-surface-100 text-surface-600"          },
  "scheduled":  { label: "Scheduled",          Icon: RefreshCw, cls: "bg-brand-50 text-brand-700 border border-brand-100" },
  "both":       { label: "On-demand + Synced", Icon: Zap,       cls: "bg-teal-50 text-teal-700 border border-teal-100"    },
};

export function IntegrationsGrid() {
  const [active, setActive] = useState("All");

  const visible = active === "All"
    ? INTEGRATIONS
    : INTEGRATIONS.filter((i) => i.category === active);

  return (
    <section className="bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        {/* Category tabs */}
        <div className="mb-10 flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActive(cat)}
              className={[
                "rounded-full px-4 py-2 text-sm font-medium transition-all",
                active === cat
                  ? "bg-surface-900 text-white shadow-sm"
                  : "border border-surface-200 bg-white text-surface-600 hover:border-surface-300 hover:text-surface-900",
              ].join(" ")}
            >
              {cat}
              {cat !== "All" && (
                <span className={`ml-1.5 text-xs ${active === cat ? "text-surface-400" : "text-surface-400"}`}>
                  {INTEGRATIONS.filter((i) => i.category === cat).length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Grid */}
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {visible.map((integration) => {
            const { label, Icon, cls } = PATTERN_META[integration.pattern];
            return (
              <div
                key={integration.id}
                className="group flex flex-col rounded-2xl border border-surface-200 bg-white p-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
              >
                {/* Header */}
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className={`h-3 w-3 rounded-full shrink-0 ${integration.dot}`} />
                    <div>
                      <p className="font-bold text-surface-900">{integration.name}</p>
                      <p className="text-xs text-surface-400 leading-snug">{integration.fullName}</p>
                    </div>
                  </div>
                  <span className="shrink-0 rounded-full bg-surface-50 border border-surface-100 px-2 py-0.5 text-[10px] font-medium text-surface-500 whitespace-nowrap">
                    {integration.tag}
                  </span>
                </div>

                {/* Description */}
                <p className="mb-5 flex-1 text-sm leading-relaxed text-surface-500">
                  {integration.description}
                </p>

                {/* Footer */}
                <div className="space-y-2.5 border-t border-surface-100 pt-4">
                  {/* Pattern */}
                  <div className="flex items-center justify-between gap-2">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${cls}`}>
                      <Icon className="h-3 w-3" />
                      {label}
                    </span>
                    <span className="text-xs text-surface-400">{integration.cadence}</span>
                  </div>
                  {/* Enables */}
                  <p className="text-xs text-surface-500">
                    <span className="font-medium text-surface-700">Enables: </span>
                    {integration.enables}
                  </p>
                  {/* Stat */}
                  <p className="text-[11px] font-semibold text-surface-400 uppercase tracking-wide">
                    {integration.stat}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Count */}
        <p className="mt-8 text-center text-sm text-surface-400">
          Showing {visible.length} of {INTEGRATIONS.length} integrations
        </p>
      </div>
    </section>
  );
}

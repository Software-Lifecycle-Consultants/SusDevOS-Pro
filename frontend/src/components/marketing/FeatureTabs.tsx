"use client";

import { useState } from "react";
import {
  BarChart3,
  Users,
  Leaf,
  CheckCircle2,
  FileText,
  Globe,
  Map,
  TreePine,
  Target,
  Key,
  Download,
  Activity,
} from "lucide-react";

const TABS = [
  {
    id:    "sustainability",
    label: "For sustainability managers",
    features: [
      { icon: BarChart3,    text: "Auto-populated DEFRA 2024, EPA eGRID and Climatiq emission factors — updated annually" },
      { icon: CheckCircle2, text: "Scope 3 relevance assessment — guided checklist for all 15 categories" },
      { icon: Target,       text: "SBTi target tracking with year-by-year milestone progress" },
      { icon: Activity,     text: "Internal approval workflow → third-party verification sign-off → immutable verified record" },
      { icon: Download,     text: "CDP-ready export — maps to C6, C7 and C10 questionnaire sections automatically" },
    ],
  },
  {
    id:    "consultant",
    label: "For ESG consultants",
    features: [
      { icon: Users,    text: "Manage up to 25 client entities from one login — switch with a click, no re-authentication" },
      { icon: FileText, text: "White-label PDF reports with your firm's logo and brand colours" },
      { icon: Globe,    text: "Client read-only portal — share results without sharing your login credentials" },
      { icon: Download, text: "Bulk CSV data import for multi-client annual reporting — no manual data entry" },
      { icon: Key,      text: "API access for custom integrations and automated data pipelines" },
    ],
  },
  {
    id:    "development",
    label: "For development projects",
    features: [
      { icon: Map,      text: "Land parcel and ecosystem mapping with PostGIS geometry — precise boundary recording" },
      { icon: TreePine, text: "Tree removal carbon stock calculations using IPCC Tier 1, 2 and 3 biomass methods" },
      { icon: Leaf,     text: "Habitat restoration sequestration tracking with 30-year IPCC growth curve projections" },
      { icon: Activity, text: "TNFD-aligned biodiversity impact reporting via the LEAP framework" },
      { icon: FileText, text: "Project carbon summary reports for planning consents and green finance documentation" },
    ],
  },
];

export function FeatureTabs() {
  const [active, setActive] = useState(TABS[0].id);
  const tab = TABS.find((t) => t.id === active)!;

  return (
    <div>
      {/* Tab buttons */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-0 sm:border-b sm:border-surface-200 mb-8">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={[
              "px-4 py-2.5 text-sm font-medium transition-colors sm:border-b-2 rounded-md sm:rounded-none",
              active === t.id
                ? "bg-brand-50 text-brand-700 sm:bg-transparent sm:border-brand-600 sm:text-brand-700"
                : "text-surface-500 hover:text-surface-800 sm:border-transparent",
            ].join(" ")}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Feature list */}
      <ul className="space-y-4">
        {tab.features.map(({ icon: Icon, text }) => (
          <li key={text} className="flex items-start gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-100">
              <Icon className="h-3.5 w-3.5 text-brand-700" />
            </span>
            <span className="text-surface-600 text-[15px] leading-relaxed">{text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

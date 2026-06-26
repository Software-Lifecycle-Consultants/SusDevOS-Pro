"use client";

import { useState } from "react";
import {
  BarChart3, Briefcase, Building2,
  CheckCircle2, FileText, Globe, Map,
  TreePine, Target, Key, Download, Activity, Users, Leaf,
} from "lucide-react";

const TABS = [
  {
    id:      "sustainability",
    role:    "Sustainability managers",
    tagline: "From data chaos to verified inventory",
    Icon:    BarChart3,
    features: [
      { Icon: BarChart3,    title: "Auto emission factors",    body: "DEFRA 2024, EPA eGRID and Climatiq — 10,000+ factors updated annually, applied automatically." },
      { Icon: CheckCircle2, title: "Scope 3 assessment",       body: "Guided relevance checklist for all 15 categories. Documented decisions, no guesswork." },
      { Icon: Target,       title: "SBTi target tracking",     body: "Year-by-year milestone progress against your 1.5°C pathway target." },
      { Icon: Activity,     title: "Verification workflow",     body: "Internal approval → third-party sign-off → immutable verified record." },
      { Icon: Download,     title: "CDP-ready export",          body: "Auto-maps to C6, C7 and C10 questionnaire sections in one click." },
      { Icon: FileText,     title: "Audit-ready PDF",           body: "Every factor, every GWP value, every boundary decision fully documented." },
    ],
  },
  {
    id:      "consultant",
    role:    "ESG consultants",
    tagline: "Multi-client management, one login",
    Icon:    Briefcase,
    features: [
      { Icon: Users,     title: "Multi-entity management", body: "Manage up to 25 client entities from one login — switch with a click, no re-auth." },
      { Icon: FileText,  title: "White-label reports",     body: "PDF reports with your firm's logo and brand colours for client delivery." },
      { Icon: Globe,     title: "Client read-only portal", body: "Share results with clients without sharing your login credentials." },
      { Icon: Download,  title: "Bulk CSV import",         body: "Multi-client annual reporting with no manual data entry." },
      { Icon: Key,       title: "API access",              body: "Custom integrations and automated data pipelines for your workflow." },
      { Icon: Activity,  title: "Change tracking",         body: "Full audit log showing every correction, who made it, and when." },
    ],
  },
  {
    id:      "development",
    role:    "Development projects",
    tagline: "Land, trees, and biodiversity unified",
    Icon:    Building2,
    features: [
      { Icon: Map,          title: "GIS land parcel mapping",  body: "PostGIS boundary recording — precise geometry for planning submissions." },
      { Icon: TreePine,     title: "Biomass carbon stocks",    body: "IPCC Tier 1, 2 and 3 methods for tree removal carbon accounting." },
      { Icon: Leaf,         title: "Restoration sequestration",body: "30-year IPCC growth curve projections for habitat restoration tracking." },
      { Icon: Activity,     title: "TNFD reporting",           body: "Biodiversity impact reporting via the LEAP framework, TNFD-aligned." },
      { Icon: FileText,     title: "Project carbon summary",   body: "Planning consent reports and green finance documentation in one click." },
      { Icon: CheckCircle2, title: "Net-zero pathway",         body: "Offset and restore tracking against project-level carbon targets." },
    ],
  },
];

export function FeatureTabs() {
  const [active, setActive] = useState(TABS[0].id);
  const tab = TABS.find((t) => t.id === active)!;

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:gap-10">
      {/* Persona selectors */}
      <div className="flex flex-row gap-2 overflow-x-auto pb-1 lg:w-64 lg:shrink-0 lg:flex-col lg:overflow-visible lg:pb-0">
        {TABS.map(({ id, role, tagline, Icon }) => {
          const isActive = id === active;
          return (
            <button
              key={id}
              onClick={() => setActive(id)}
              className={[
                "flex shrink-0 items-start gap-3 rounded-xl border p-4 text-left transition-all duration-200 lg:shrink",
                isActive
                  ? "border-brand-600 bg-brand-600 shadow-md shadow-brand-600/20"
                  : "border-surface-200 bg-white hover:border-brand-300 hover:bg-brand-50",
              ].join(" ")}
            >
              <div className={[
                "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                isActive ? "bg-white/20" : "bg-brand-100",
              ].join(" ")}>
                <Icon className={`h-4 w-4 ${isActive ? "text-white" : "text-brand-700"}`} />
              </div>
              <div>
                <p className={`text-sm font-semibold leading-tight ${isActive ? "text-white" : "text-surface-900"}`}>
                  {role}
                </p>
                <p className={`mt-0.5 text-xs leading-snug ${isActive ? "text-brand-100" : "text-surface-500"}`}>
                  {tagline}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Feature cards */}
      <div className="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-2">
        {tab.features.map(({ Icon, title, body }) => (
          <div
            key={title}
            className="group rounded-xl border border-surface-200 bg-white p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md"
          >
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 transition-colors group-hover:bg-brand-100">
              <Icon className="h-[18px] w-[18px] text-brand-600" />
            </div>
            <p className="mb-1 text-sm font-semibold text-surface-900">{title}</p>
            <p className="text-sm leading-relaxed text-surface-500">{body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

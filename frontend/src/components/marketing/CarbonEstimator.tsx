"use client";

import { useState } from "react";
import { Calculator, ArrowRight } from "lucide-react";

const SECTORS = [
  { value: "property",       label: "Property & real estate",        scopeMultiplier: 1.2 },
  { value: "construction",   label: "Construction & infrastructure",  scopeMultiplier: 2.1 },
  { value: "manufacturing",  label: "Manufacturing",                  scopeMultiplier: 3.4 },
  { value: "retail",         label: "Retail & consumer goods",        scopeMultiplier: 2.8 },
  { value: "professional",   label: "Professional services",          scopeMultiplier: 0.6 },
  { value: "finance",        label: "Financial services",             scopeMultiplier: 0.9 },
  { value: "transport",      label: "Transport & logistics",          scopeMultiplier: 4.2 },
  { value: "energy",         label: "Energy & utilities",             scopeMultiplier: 5.1 },
  { value: "food",           label: "Food & agriculture",             scopeMultiplier: 3.9 },
  { value: "tech",           label: "Technology & software",          scopeMultiplier: 0.5 },
  { value: "healthcare",     label: "Healthcare",                     scopeMultiplier: 1.1 },
  { value: "other",          label: "Other",                          scopeMultiplier: 1.5 },
];

const EMPLOYEE_RANGES = [
  { value: "5",    label: "1–10 employees",   mid: 5    },
  { value: "30",   label: "11–50 employees",  mid: 30   },
  { value: "125",  label: "51–200 employees", mid: 125  },
  { value: "350",  label: "201–500 employees",mid: 350  },
  { value: "750",  label: "500+ employees",   mid: 750  },
];

const COUNTRIES = [
  { value: "GB", label: "United Kingdom",  gridEf: 0.207 },
  { value: "US", label: "United States",   gridEf: 0.388 },
  { value: "DE", label: "Germany",         gridEf: 0.364 },
  { value: "FR", label: "France",          gridEf: 0.052 },
  { value: "AU", label: "Australia",       gridEf: 0.610 },
  { value: "CA", label: "Canada",          gridEf: 0.130 },
  { value: "IN", label: "India",           gridEf: 0.708 },
  { value: "CN", label: "China",           gridEf: 0.556 },
  { value: "EU", label: "EU (other)",      gridEf: 0.276 },
  { value: "XX", label: "Other / global",  gridEf: 0.410 },
];

function estimateCO2e(sector: string, employees: string, country: string): { low: number; high: number } | null {
  const s = SECTORS.find((x) => x.value === sector);
  const e = EMPLOYEE_RANGES.find((x) => x.value === employees);
  const c = COUNTRIES.find((x) => x.value === country);
  if (!s || !e || !c) return null;

  // Base: ~4 tCO2e per employee per year (UK avg Scope 1+2, approximate)
  const base = e.mid * 4 * s.scopeMultiplier;
  // Adjust Scope 2 for grid EF vs UK baseline
  const gridAdjustment = (c.gridEf / 0.207) * 0.3;
  const mid = base * (0.85 + gridAdjustment * 0.15);

  return {
    low:  Math.round(mid * 0.6  / 10) * 10,
    high: Math.round(mid * 1.45 / 10) * 10,
  };
}

export function CarbonEstimator() {
  const [sector,    setSector]    = useState("");
  const [employees, setEmployees] = useState("");
  const [country,   setCountry]   = useState("");
  const [result,    setResult]    = useState<{ low: number; high: number } | null>(null);

  const canEstimate = sector && employees && country;

  function handleEstimate() {
    setResult(estimateCO2e(sector, employees, country));
  }

  const selectClass =
    "w-full rounded-md border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

  return (
    <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6 sm:p-8 max-w-xl mx-auto">
      <div className="flex items-center gap-2 mb-6">
        <Calculator className="h-5 w-5 text-brand-600" />
        <h3 className="font-semibold text-surface-900">Estimate your carbon footprint</h3>
      </div>

      <div className="space-y-4">
        {/* Sector */}
        <div>
          <label className="block text-sm text-surface-600 mb-1.5">Industry sector</label>
          <select value={sector} onChange={(e) => setSector(e.target.value)} className={selectClass}>
            <option value="">Select a sector…</option>
            {SECTORS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Employees */}
        <div>
          <label className="block text-sm text-surface-600 mb-1.5">Number of employees</label>
          <select value={employees} onChange={(e) => setEmployees(e.target.value)} className={selectClass}>
            <option value="">Select a range…</option>
            {EMPLOYEE_RANGES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm text-surface-600 mb-1.5">Country</label>
          <select value={country} onChange={(e) => setCountry(e.target.value)} className={selectClass}>
            <option value="">Select a country…</option>
            {COUNTRIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handleEstimate}
          disabled={!canEstimate}
          className="w-full bg-brand-600 text-white py-2.5 rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          Calculate estimate
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="mt-6 rounded-xl bg-brand-50 border border-brand-100 p-5">
          <p className="text-xs uppercase tracking-wide text-brand-600 font-medium mb-1">
            Estimated Scope 1 + 2 footprint
          </p>
          <p className="text-3xl font-bold text-brand-800 mb-1">
            {result.low.toLocaleString()}–{result.high.toLocaleString()} tCO₂e
          </p>
          <p className="text-xs text-brand-700 mb-4">per year (indicative range)</p>
          <p className="text-xs text-surface-500 mb-4">
            This is a rough estimate based on industry averages and does not include Scope 3 emissions,
            which typically account for 70–90% of a company&apos;s total footprint.
            Get your precise, audit-ready inventory in SusDevOS.
          </p>
          <a
            href="/register"
            className="inline-flex items-center gap-1.5 bg-brand-600 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-brand-700 transition-colors"
          >
            Get my precise inventory — free
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
        </div>
      )}
    </div>
  );
}

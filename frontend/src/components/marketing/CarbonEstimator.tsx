"use client";

import { useState } from "react";
import { Leaf, ArrowRight, Info } from "lucide-react";

// ─────────────────────────────────────────────────────────────────────────────
// IPCC 2006 LULUCF Tier 1 parameters
// peakRate  = tCO₂/ha/yr at full maturity (above-ground + below-ground biomass)
// matureYrs = years to reach peak rate (linear ramp-up assumption)
// ─────────────────────────────────────────────────────────────────────────────

interface Ecosystem {
  label:       string;
  peakRate:    number;
  matureYrs:   number;
  description: string;
  source:      string;
}

const ECOSYSTEMS: Record<string, Ecosystem> = {
  woodland_broadleaf: {
    label:       "Temperate woodland — broadleaf",
    peakRate:    6.5,
    matureYrs:   25,
    description: "Oak, ash, beech and mixed broadleaf. UK, Europe, North America.",
    source:      "IPCC 2006 Table 4.7 (temperate moist, broadleaf)",
  },
  woodland_conifer: {
    label:       "Temperate woodland — conifer",
    peakRate:    7.5,
    matureYrs:   25,
    description: "Spruce, pine, larch plantation or natural regeneration.",
    source:      "IPCC 2006 Table 4.7 (temperate moist, conifer)",
  },
  tropical_forest: {
    label:       "Tropical forest",
    peakRate:    12.0,
    matureYrs:   20,
    description: "Tropical moist forest restoration. SE Asia, Latin America, Africa.",
    source:      "IPCC 2006 Table 4.7 (tropical moist, broadleaf)",
  },
  grassland: {
    label:       "Grassland restoration",
    peakRate:    1.2,
    matureYrs:   10,
    description: "Native grassland, meadow, or savanna restoration. Soil carbon dominant.",
    source:      "IPCC 2006 Chapter 6 (grassland carbon)",
  },
  peatland: {
    label:       "Peatland restoration",
    peakRate:    1.6,
    matureYrs:   15,
    description: "Rewetting degraded peat bogs and fens. Highly variable by site.",
    source:      "IPCC 2006 Table 7.2 (drained organic soils rewetted)",
  },
  wetland: {
    label:       "Freshwater wetland",
    peakRate:    3.0,
    matureYrs:   12,
    description: "Reed beds, fen, floodplain restoration. Belowground biomass dominant.",
    source:      "IPCC 2006 Chapter 7 (wetlands)",
  },
  coastal: {
    label:       "Coastal / Blue carbon",
    peakRate:    8.5,
    matureYrs:   12,
    description: "Mangrove, saltmarsh, seagrass. Tropical and subtropical coasts.",
    source:      "IPCC 2013 Wetlands Supplement (coastal wetlands)",
  },
  heathland: {
    label:       "Heathland / Moorland",
    peakRate:    1.0,
    matureYrs:   12,
    description: "Upland and lowland heath, heather moorland. UK and Northern Europe.",
    source:      "IPCC 2006 Chapter 6 (shrubland carbon)",
  },
  mixed: {
    label:       "Mixed habitats",
    peakRate:    3.5,
    matureYrs:   15,
    description: "Multi-habitat mosaic: woodland, grassland, scrub, and wetland patches.",
    source:      "IPCC 2006 (weighted average across habitat types)",
  },
};

// Cumulative sequestration at year N for a given ecosystem and area
function cumulativeAtYear(eco: Ecosystem, hectares: number, year: number): number {
  let total = 0;
  for (let y = 1; y <= year; y++) {
    const growthFactor = Math.min(1, y / eco.matureYrs);
    total += eco.peakRate * growthFactor * hectares;
  }
  return Math.round(total);
}

// ─────────────────────────────────────────────────────────────────────────────

export function CarbonEstimator() {
  const [ecosystemKey, setEcosystemKey] = useState("");
  const [hectares,     setHectares]     = useState("");
  const [result,       setResult]       = useState<null | {
    y10: number; y20: number; y30: number;
    peakAnnual: number; eco: Ecosystem;
  }>(null);

  const canEstimate = ecosystemKey && Number(hectares) > 0;

  function handleEstimate() {
    const eco = ECOSYSTEMS[ecosystemKey];
    const ha  = Number(hectares);
    if (!eco || !ha) return;
    setResult({
      y10:        cumulativeAtYear(eco, ha, 10),
      y20:        cumulativeAtYear(eco, ha, 20),
      y30:        cumulativeAtYear(eco, ha, 30),
      peakAnnual: Math.round(eco.peakRate * ha),
      eco,
    });
  }

  return (
    <div className="mx-auto max-w-xl rounded-2xl border border-surface-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-6 flex items-center gap-2">
        <Leaf className="h-5 w-5 text-brand-600" />
        <h3 className="font-semibold text-surface-900">
          Estimate project carbon sequestration
        </h3>
      </div>

      <div className="space-y-4">
        {/* Ecosystem type */}
        <div>
          <label className="mb-1.5 block text-sm text-surface-600">
            Ecosystem / habitat type
          </label>
          <select
            value={ecosystemKey}
            onChange={(e) => { setEcosystemKey(e.target.value); setResult(null); }}
            className="w-full rounded-md border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-800 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          >
            <option value="">Select ecosystem…</option>
            {Object.entries(ECOSYSTEMS).map(([key, eco]) => (
              <option key={key} value={key}>{eco.label}</option>
            ))}
          </select>
          {ecosystemKey && (
            <p className="mt-1 text-xs text-surface-400">
              {ECOSYSTEMS[ecosystemKey].description}
            </p>
          )}
        </div>

        {/* Area */}
        <div>
          <label className="mb-1.5 block text-sm text-surface-600">
            Project area (hectares)
          </label>
          <input
            type="number"
            min={0.1}
            step="any"
            placeholder="e.g. 50"
            value={hectares}
            onChange={(e) => { setHectares(e.target.value); setResult(null); }}
            className="w-full rounded-md border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-800 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>

        <button
          onClick={handleEstimate}
          disabled={!canEstimate}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Calculate estimate
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-6 rounded-xl border border-brand-100 bg-brand-50 p-5">
          {/* Headline */}
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600">
            Estimated 30-year sequestration
          </p>
          <p className="text-3xl font-bold text-brand-800">
            {result.y30.toLocaleString()} tCO₂e
          </p>
          <p className="mb-5 mt-0.5 text-xs text-brand-600">
            Peak rate: ~{result.peakAnnual.toLocaleString()} tCO₂e/year at maturity
          </p>

          {/* Progress milestones */}
          <div className="space-y-3">
            {[
              { label: "Year 10", value: result.y10, total: result.y30 },
              { label: "Year 20", value: result.y20, total: result.y30 },
              { label: "Year 30", value: result.y30, total: result.y30 },
            ].map(({ label, value, total }) => (
              <div key={label}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-brand-700 font-medium">{label}</span>
                  <span className="tabular-nums text-brand-800 font-semibold">
                    {value.toLocaleString()} tCO₂e
                    <span className="ml-1 font-normal text-brand-500">
                      ({Math.round((value / total) * 100)}%)
                    </span>
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-brand-200">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all"
                    style={{ width: `${(value / total) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* IPCC source + disclaimer */}
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-brand-200 bg-white/60 p-3">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
            <p className="text-[11px] leading-relaxed text-surface-500">
              Indicative estimate based on <strong>{result.eco.source}</strong> (IPCC Tier 1).
              Actual sequestration varies significantly with site conditions, species mix,
              and management. For a verified project methodology, use SusDevOS or consult
              a Verra/Gold Standard validator.
            </p>
          </div>

          <a
            href="/register"
            className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-700"
          >
            Track this project in SusDevOS — free
            <ArrowRight className="h-3.5 w-3.5" />
          </a>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { Search, ExternalLink, Copy, Check } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import type { EmissionFactor } from "@/components/emissions/EFPicker";

interface EFSet { SetId: number; SetName: string; Publisher: string; ApplicableYear: number | null; }

const SCOPE_LABELS: Record<string, string> = {
  "":  "All scopes",
  "1": "Scope 1",
  "2": "Scope 2",
  "3": "Scope 3",
};

const S3_CATEGORIES = [
  "1: Purchased goods", "2: Capital goods", "3: Fuel & energy",
  "4: Upstream transport", "5: Waste", "6: Business travel",
  "7: Employee commuting", "8: Upstream leased assets", "9: Downstream transport",
  "10: Processing sold products", "11: Use of sold products", "12: End-of-life treatment",
  "13: Downstream leased assets", "14: Franchises", "15: Investments",
];

function useCopyToClipboard(timeout = 2000) {
  const [copied, setCopied] = useState<string | null>(null);
  function copy(text: string, key: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), timeout);
    });
  }
  return { copied, copy };
}

export default function EmissionFactorsPage() {
  const { activeEntityId } = useAuthStore();
  const { copied, copy } = useCopyToClipboard();

  const [search,  setSearch]  = useState("");
  const [scope,   setScope]   = useState("");
  const [scope3,  setScope3]  = useState("");
  const [setId,   setSetId]   = useState("");
  const [page,    setPage]    = useState(1);
  const PAGE_SIZE = 25;

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [search, scope, scope3, setId]);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  // Fetch factor sets for the filter dropdown
  const { data: setsData } = useQuery({
    queryKey: ["ef-sets"],
    queryFn: () =>
      axiosInstance.get<{ results: EFSet[] }>("/api/emission-factor-sets/?page_size=100", { headers })
        .then((r) => r.data),
  });

  // Fetch factors
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["emission-factors", search, scope, scope3, setId, page],
    queryFn: () => {
      const params = new URLSearchParams();
      if (search)  params.set("search",    search);
      if (scope)   params.set("scope",     scope);
      if (scope3)  params.set("scope3",    scope3);
      if (setId)   params.set("set_id",    setId);
      params.set("page",      String(page));
      params.set("page_size", String(PAGE_SIZE));
      return axiosInstance
        .get<{ results: EmissionFactor[]; count: number }>(`/api/emission-factors/?${params}`, { headers })
        .then((r) => r.data);
    },
    placeholderData: (prev) => prev,
  });

  const factors   = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);
  const sets       = setsData?.results ?? [];

  const inputClass = "h-9 rounded-md border border-surface-200 bg-white px-3 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <h1 className="page-title">Emission factor library</h1>
        <p className="page-subtitle">
          {totalCount.toLocaleString()} factors across DEFRA, EPA eGRID, Climatiq and IPCC sources.
          Select a factor when creating an emissions record.
        </p>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-end">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <label className="label mb-1">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-400" />
            <input
              type="text"
              className={`${inputClass} pl-9 w-full`}
              placeholder="Natural gas, electricity, flights…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Scope */}
        <div>
          <label className="label mb-1">Scope</label>
          <select className={inputClass} value={scope} onChange={(e) => { setScope(e.target.value); setScope3(""); }}>
            {Object.entries(SCOPE_LABELS).map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </div>

        {/* Scope 3 category */}
        {scope === "3" && (
          <div>
            <label className="label mb-1">Category</label>
            <select className={inputClass} value={scope3} onChange={(e) => setScope3(e.target.value)}>
              <option value="">All categories</option>
              {S3_CATEGORIES.map((c, i) => (
                <option key={i + 1} value={String(i + 1)}>{c}</option>
              ))}
            </select>
          </div>
        )}

        {/* Factor set */}
        <div>
          <label className="label mb-1">Source</label>
          <select className={inputClass} value={setId} onChange={(e) => setSetId(e.target.value)}>
            <option value="">All sources</option>
            {sets.map((s) => (
              <option key={s.SetId} value={String(s.SetId)}>
                {s.SetName}{s.ApplicableYear ? ` (${s.ApplicableYear})` : ""}
              </option>
            ))}
          </select>
        </div>

        {(search || scope || setId) && (
          <button
            className="h-9 px-3 text-sm text-surface-500 hover:text-surface-800 border border-surface-200 rounded-md"
            onClick={() => { setSearch(""); setScope(""); setScope3(""); setSetId(""); }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[800px]">
            <thead>
              <tr className="border-b border-surface-200 bg-surface-50">
                <th className="text-left px-4 py-3 font-medium text-surface-500 w-72">Activity</th>
                <th className="text-left px-4 py-3 font-medium text-surface-500">Category</th>
                <th className="text-center px-3 py-3 font-medium text-surface-500 w-24">Scope</th>
                <th className="text-left px-3 py-3 font-medium text-surface-500 w-20">Gas</th>
                <th className="text-right px-4 py-3 font-medium text-surface-500 w-36">
                  Factor (kg CO₂e)
                </th>
                <th className="text-left px-3 py-3 font-medium text-surface-500 w-20">Unit</th>
                <th className="text-left px-3 py-3 font-medium text-surface-500 w-24">Year</th>
                <th className="text-left px-4 py-3 font-medium text-surface-500">Source</th>
                <th className="w-20" />
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-100">
              {isLoading && (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-sm text-surface-400">
                    Loading emission factors…
                  </td>
                </tr>
              )}
              {!isLoading && factors.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-sm text-surface-400">
                    No emission factors match your filters.
                    {!search && !scope && !setId && (
                      <span className="block mt-1 text-xs">
                        Run <code className="bg-surface-100 px-1 rounded">seed_gwp</code> and sync the DEFRA integration to populate the library.
                      </span>
                    )}
                  </td>
                </tr>
              )}
              {factors.map((ef) => {
                const copyKey = `ef-${ef.FactorId}`;
                return (
                  <tr key={ef.FactorId} className={`hover:bg-surface-50 ${isFetching ? "opacity-60" : ""}`}>
                    <td className="px-4 py-3">
                      <p className="font-medium text-surface-800 leading-snug">{ef.ActivityName}</p>
                    </td>
                    <td className="px-4 py-3 text-surface-500 text-xs max-w-[160px]">
                      {ef.ActivityCategory || "—"}
                    </td>
                    <td className="px-3 py-3 text-center">
                      <span className="badge badge-slate text-xs">
                        Sc.{ef.Scope}{ef.Scope3Category ? ` C${ef.Scope3Category}` : ""}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-surface-600 text-xs">
                      {ef.Gas}{ef.GasSubtype ? <span className="text-surface-400"> ({ef.GasSubtype})</span> : null}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-surface-800 tabular-nums">
                      {parseFloat(ef.FactorValue).toFixed(6)}
                    </td>
                    <td className="px-3 py-3 text-surface-500 text-xs">{ef.unit ?? "—"}</td>
                    <td className="px-3 py-3 text-surface-400 text-xs">{ef.ApplicableYear ?? "—"}</td>
                    <td className="px-4 py-3 text-surface-500 text-xs">{ef.set_name}</td>
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        title="Copy factor value"
                        onClick={() => copy(ef.FactorValue, copyKey)}
                        className="p-1.5 rounded text-surface-400 hover:text-surface-700 hover:bg-surface-100 transition-colors"
                      >
                        {copied === copyKey
                          ? <Check className="h-4 w-4 text-brand-500" />
                          : <Copy className="h-4 w-4" />
                        }
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-surface-100 px-4 py-3 flex items-center justify-between text-sm">
            <p className="text-surface-500">
              Showing {((page - 1) * PAGE_SIZE) + 1}–{Math.min(page * PAGE_SIZE, totalCount)} of {totalCount.toLocaleString()}
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 rounded border border-surface-200 text-surface-600 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 rounded border border-surface-200 text-surface-600 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Info banner */}
      <div className="rounded-lg border border-surface-200 bg-surface-50 px-4 py-3 flex items-start gap-3 text-sm">
        <ExternalLink className="h-4 w-4 text-surface-400 mt-0.5 shrink-0" />
        <div className="text-surface-500">
          <span className="font-medium text-surface-700">Sources: </span>
          DEFRA Greenhouse Gas Conversion Factors (annual), EPA eGRID (US electricity), IPCC 2006 LULUCF tables.
          Factors are synced automatically — run <code className="bg-surface-100 px-1 rounded text-xs">seed_gwp</code> locally
          or check Settings → Integrations for sync status.
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X, ChevronDown } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

export interface EmissionFactor {
  FactorId:       number;
  SetId:          number;
  set_name:       string;
  set_publisher:  string;
  ActivityName:   string;
  ActivityCategory: string | null;
  Scope:          number;
  Scope3Category: number | null;
  Gas:            string;
  GasSubtype:     string | null;
  FactorValue:    string;
  unit:           string | null;
  CountryCode:    string | null;
  ApplicableYear: number | null;
}

interface Props {
  scope?:    number;          // pre-filter by scope
  value?:    EmissionFactor | null;
  onChange:  (ef: EmissionFactor | null) => void;
  disabled?: boolean;
}

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export function EFPicker({ scope, value, onChange, disabled }: Props) {
  const { activeEntityId } = useAuthStore();
  const [open,   setOpen]   = useState(false);
  const [query,  setQuery]  = useState("");
  const [items,  setItems]  = useState<EmissionFactor[]>([]);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const debouncedQuery = useDebounce(query, 300);

  // Fetch when query or scope changes
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    const params = new URLSearchParams();
    if (debouncedQuery) params.set("search", debouncedQuery);
    if (scope)          params.set("scope",  String(scope));
    params.set("page_size", "30");

    axiosInstance
      .get<{ results: EmissionFactor[] }>(`/api/emission-factors/?${params}`, {
        headers: activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {},
      })
      .then((r) => setItems(r.data.results ?? []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [debouncedQuery, scope, open, activeEntityId]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function select(ef: EmissionFactor) {
    onChange(ef);
    setOpen(false);
    setQuery("");
  }

  function clear(e: React.MouseEvent) {
    e.stopPropagation();
    onChange(null);
  }

  // ── Selected state
  if (value && !open) {
    return (
      <div
        className="input flex items-center justify-between gap-2 cursor-pointer"
        onClick={() => !disabled && setOpen(true)}
      >
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-surface-800">{value.ActivityName}</p>
          <p className="text-xs text-surface-400 truncate">
            {value.FactorValue} kg CO₂e/{value.unit ?? "unit"} · {value.set_name}
          </p>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={clear}
            className="shrink-0 text-surface-400 hover:text-surface-600"
            aria-label="Clear selection"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  // ── Picker open state
  return (
    <div ref={containerRef} className="relative">
      <div
        className="input flex items-center gap-2 cursor-pointer"
        onClick={() => !disabled && setOpen(true)}
      >
        <Search className="h-4 w-4 text-surface-400 shrink-0" />
        {open ? (
          <input
            autoFocus
            type="text"
            className="flex-1 bg-transparent outline-none text-sm text-surface-800 placeholder:text-surface-400"
            placeholder="Search by activity (e.g. natural gas, electricity…)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="flex-1 text-sm text-surface-400">Search emission factors…</span>
        )}
        <ChevronDown className="h-4 w-4 text-surface-400 shrink-0" />
      </div>

      {open && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border border-surface-200 bg-white shadow-lg overflow-hidden">
          {loading && (
            <div className="px-4 py-3 text-xs text-surface-400">Searching…</div>
          )}

          {!loading && items.length === 0 && (
            <div className="px-4 py-3 text-xs text-surface-400">
              {query ? "No factors found. Try a different search term." : "Start typing to search the emission factor library."}
            </div>
          )}

          <ul className="max-h-72 overflow-y-auto divide-y divide-surface-100">
            {items.map((ef) => (
              <li key={ef.FactorId}>
                <button
                  type="button"
                  onClick={() => select(ef)}
                  className="w-full text-left px-4 py-3 hover:bg-surface-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-surface-800 truncate">{ef.ActivityName}</p>
                      {ef.ActivityCategory && (
                        <p className="text-xs text-surface-400 truncate">{ef.ActivityCategory}</p>
                      )}
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-sm font-mono text-surface-700">
                        {parseFloat(ef.FactorValue).toFixed(4)}
                      </p>
                      <p className="text-xs text-surface-400">
                        kg CO₂e/{ef.unit ?? "unit"}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-1.5 flex-wrap">
                    <span className="text-[11px] bg-surface-100 text-surface-500 px-1.5 py-0.5 rounded">
                      {ef.Gas}{ef.GasSubtype ? ` (${ef.GasSubtype})` : ""}
                    </span>
                    <span className="text-[11px] bg-brand-50 text-brand-600 px-1.5 py-0.5 rounded">
                      Scope {ef.Scope}{ef.Scope3Category ? ` Cat.${ef.Scope3Category}` : ""}
                    </span>
                    <span className="text-[11px] bg-surface-100 text-surface-500 px-1.5 py-0.5 rounded">
                      {ef.set_name}{ef.ApplicableYear ? ` ${ef.ApplicableYear}` : ""}
                    </span>
                    {ef.CountryCode && (
                      <span className="text-[11px] bg-surface-100 text-surface-500 px-1.5 py-0.5 rounded">
                        {ef.CountryCode}
                      </span>
                    )}
                  </div>
                </button>
              </li>
            ))}
          </ul>

          {items.length > 0 && (
            <div className="border-t border-surface-100 px-4 py-2 flex items-center justify-between">
              <p className="text-xs text-surface-400">Showing up to 30 results</p>
              <a
                href="/emission-factors"
                target="_blank"
                className="text-xs text-brand-600 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                Browse full library →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

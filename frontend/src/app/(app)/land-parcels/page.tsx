"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Map, List, X, MapPin, FileText } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { EmptyState } from "@/components/EmptyState";

const LandMap = dynamic(() => import("@/components/land/LandMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[520px] rounded-xl border border-surface-200 bg-surface-50 flex items-center justify-center text-sm text-surface-400">
      Loading map…
    </div>
  ),
});

const MapPicker = dynamic(() => import("@/components/land/MapPicker"), {
  ssr: false,
  loading: () => (
    <div className="h-[280px] rounded-lg border border-surface-200 bg-surface-50 flex items-center justify-center text-sm text-surface-400">
      Loading map…
    </div>
  ),
});

interface LandParcel {
  LandParcelId:      number;
  ParcelName:        string;
  ParcelReference:   string | null;
  AreaHectares:      string | null;
  LandUseType:       string | null;
  Tenure:            string | null;
  PlanningReference: string | null;
  BoundaryGeoJSON:   object | null;
  Status:            number;
}

const LAND_USE_TYPES = [
  "Woodland", "Grassland", "Wetland", "Peatland",
  "Heathland / Moorland", "Coastal / Marine",
  "Agricultural", "Greenfield", "Brownfield", "Urban", "Mixed", "Other",
];

const TENURES = [
  "Freehold", "Leasehold", "Licensed",
  "Management Agreement", "Conservation Easement", "Other",
];

type Tab = "details" | "location";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "details",  label: "Parcel Details",      icon: <FileText className="h-3.5 w-3.5" /> },
  { id: "location", label: "Location & Boundary", icon: <MapPin   className="h-3.5 w-3.5" /> },
];

function CreateParcelModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<Tab>("details");
  const [form, setForm] = useState({
    ParcelName: "", ParcelReference: "", AreaHectares: "",
    LandUseType: "", Tenure: "", PlanningReference: "", Description: "",
    BoundaryGeoJSON: "",
  });
  const [geoError, setGeoError] = useState<string | null>(null);
  const [error, setError]       = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => {
      let boundary: object | null = null;
      if (form.BoundaryGeoJSON.trim()) {
        try { boundary = JSON.parse(form.BoundaryGeoJSON); }
        catch { throw new Error("Invalid GeoJSON"); }
      }
      return axiosInstance.post("/api/land-parcels/", {
        ParcelName:        form.ParcelName,
        ParcelReference:   form.ParcelReference   || null,
        AreaHectares:      form.AreaHectares       ? Number(form.AreaHectares) : null,
        LandUseType:       form.LandUseType        || null,
        Tenure:            form.Tenure             || null,
        PlanningReference: form.PlanningReference  || null,
        Description:       form.Description        || null,
        BoundaryGeoJSON:   boundary,
      }, { headers });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["land-parcels", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      if (err instanceof Error && err.message === "Invalid GeoJSON") {
        setGeoError("Invalid GeoJSON — paste a valid Polygon, MultiPolygon, or Point.");
        setTab("location");
        return;
      }
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? (first[0] as string) : "Failed to create parcel.");
    },
  });

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
    if (k === "BoundaryGeoJSON") setGeoError(null);
  }

  function handleMapChange(geojson: string) {
    set("BoundaryGeoJSON", geojson);
  }

  const hasLocation = !!form.BoundaryGeoJSON.trim();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex w-full max-w-2xl flex-col rounded-xl bg-white shadow-2xl max-h-[90vh]">
        {/* Header */}
        <div className="flex shrink-0 items-start justify-between border-b border-surface-100 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-surface-900">Add Land Parcel</h2>
            <p className="mt-0.5 text-xs text-surface-400">
              Land parcels are geographic references used by Projects, Tree Removals, and Restorations.
            </p>
          </div>
          <button onClick={onClose} className="btn-ghost btn-sm mt-0.5">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex shrink-0 border-b border-surface-100 px-6">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 border-b-2 -mb-px py-2.5 px-3 text-sm font-medium transition-colors ${
                tab === t.id
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-surface-500 hover:text-surface-700"
              }`}
            >
              {t.icon}
              {t.label}
              {t.id === "location" && hasLocation && (
                <span className="ml-1 h-1.5 w-1.5 rounded-full bg-brand-500" />
              )}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          {error && (
            <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          )}

          <form id="parcel-form" onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }}>
            {/* Details tab */}
            {tab === "details" && (
              <div className="space-y-4">
                <div>
                  <label className="label mb-1">Parcel name <span className="text-red-400">*</span></label>
                  <input className="input" required placeholder="e.g. Site A — Development footprint"
                    value={form.ParcelName} onChange={(e) => set("ParcelName", e.target.value)} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">
                      Reference <span className="font-normal text-surface-400">optional</span>
                    </label>
                    <input className="input" placeholder="e.g. PARCEL-001"
                      value={form.ParcelReference} onChange={(e) => set("ParcelReference", e.target.value)} />
                  </div>
                  <div>
                    <label className="label mb-1">Area (hectares)</label>
                    <input className="input" type="number" step="any" min="0" placeholder="0.00"
                      value={form.AreaHectares} onChange={(e) => set("AreaHectares", e.target.value)} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Land use type</label>
                    <select className="input" value={form.LandUseType} onChange={(e) => set("LandUseType", e.target.value)}>
                      <option value="">— select —</option>
                      {LAND_USE_TYPES.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="label mb-1">Tenure</label>
                    <select className="input" value={form.Tenure} onChange={(e) => set("Tenure", e.target.value)}>
                      <option value="">— select —</option>
                      {TENURES.map((t) => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="label mb-1">
                    Planning reference <span className="font-normal text-surface-400">optional</span>
                  </label>
                  <input className="input" placeholder="e.g. 22/01234/FUL"
                    value={form.PlanningReference} onChange={(e) => set("PlanningReference", e.target.value)} />
                </div>
                <div>
                  <label className="label mb-1">
                    Description <span className="font-normal text-surface-400">optional</span>
                  </label>
                  <textarea className="input resize-y min-h-[72px]" rows={3}
                    placeholder="Describe the parcel — ownership context, ecological notes, planning history…"
                    value={form.Description} onChange={(e) => set("Description", e.target.value)} />
                </div>
              </div>
            )}

            {/* Location tab */}
            {tab === "location" && (
              <div className="space-y-4">
                <div>
                  <label className="label mb-1.5">Click the map to pin this parcel&apos;s location</label>
                  <MapPicker value={form.BoundaryGeoJSON} onChange={handleMapChange} />
                  <p className="mt-1.5 text-xs text-surface-400">
                    Click anywhere on the map to drop a pin. For precise polygon boundaries, paste GeoJSON below.
                  </p>
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center" aria-hidden>
                    <div className="w-full border-t border-surface-100" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-2 text-xs text-surface-400">or paste GeoJSON polygon</span>
                  </div>
                </div>

                <div>
                  <label className="label mb-1">Boundary GeoJSON</label>
                  <textarea
                    className={`input font-mono text-xs resize-y min-h-[100px] ${geoError ? "border-red-400" : ""}`}
                    placeholder='{"type":"Polygon","coordinates":[[[lng,lat],[lng,lat],…]]}'
                    rows={5}
                    value={form.BoundaryGeoJSON}
                    onChange={(e) => set("BoundaryGeoJSON", e.target.value)}
                  />
                  {geoError && <p className="mt-1 text-xs text-red-600">{geoError}</p>}
                  {!geoError && (
                    <p className="mt-1 text-xs text-surface-400">
                      Export from QGIS, geojson.io, or OS Maps. Supports Polygon, MultiPolygon, or Point.
                    </p>
                  )}
                </div>

                {hasLocation && !geoError && (
                  <div className="flex items-center gap-2 rounded-md bg-brand-50 border border-brand-100 px-3 py-2">
                    <MapPin className="h-3.5 w-3.5 text-brand-600 shrink-0" />
                    <span className="text-xs text-brand-700">Location captured — will be saved with this parcel.</span>
                  </div>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Footer */}
        <div className="shrink-0 flex items-center justify-between border-t border-surface-100 bg-surface-50 px-6 py-4">
          <button
            type="button"
            onClick={() => setTab(tab === "details" ? "location" : "details")}
            className="btn-secondary btn-sm"
          >
            {tab === "details" ? "Next: Location →" : "← Back to Details"}
          </button>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button form="parcel-form" type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save parcel"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LandParcelsPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [view, setView] = useState<"list" | "map">("list");

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: LandParcel[] }>({
    queryKey: ["land-parcels", activeEntityId],
    queryFn: () => axiosInstance.get("/api/land-parcels/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const softDelete = useMutation({
    mutationFn: (id: number) => axiosInstance.delete(`/api/land-parcels/${id}/`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["land-parcels", activeEntityId] }),
  });

  const parcels = (data?.results ?? []).filter((p) => p.Status < 4);
  const mappedCount = parcels.filter((p) => p.BoundaryGeoJSON).length;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Land Parcels</h1>
          <p className="page-subtitle">
            {parcels.length} parcel{parcels.length !== 1 ? "s" : ""}
            {mappedCount > 0 && ` · ${mappedCount} mapped`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-md border border-surface-200 overflow-hidden">
            <button
              className={`px-3 py-1.5 text-sm flex items-center gap-1.5 ${view === "list" ? "bg-surface-100 text-surface-900" : "bg-white text-surface-500 hover:bg-surface-50"}`}
              onClick={() => setView("list")}
            >
              <List className="h-4 w-4" /> List
            </button>
            <button
              className={`px-3 py-1.5 text-sm flex items-center gap-1.5 border-l border-surface-200 ${view === "map" ? "bg-surface-100 text-surface-900" : "bg-white text-surface-500 hover:bg-surface-50"}`}
              onClick={() => setView("map")}
            >
              <Map className="h-4 w-4" /> Map
            </button>
          </div>
          <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4" /> New parcel
          </button>
        </div>
      </div>

      {/* Map view */}
      {view === "map" && (
        parcels.length === 0
          ? <div className="card p-6 text-sm text-surface-500">No parcels to show on the map.</div>
          : <LandMap parcels={parcels} />
      )}

      {/* List view */}
      {view === "list" && (
        <div className="card overflow-hidden">
          {isLoading ? (
            <div className="p-6 text-sm text-surface-500">Loading…</div>
          ) : parcels.length === 0 ? (
            <EmptyState message="No land parcels yet." action={{ label: "+ New parcel", href: "#" }} />
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Reference</th>
                  <th className="text-right">Area (ha)</th>
                  <th>Land use</th>
                  <th>Tenure</th>
                  <th>Planning ref</th>
                  <th>Boundary</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {parcels.map((p) => (
                  <tr key={p.LandParcelId}>
                    <td className="font-medium text-surface-900">{p.ParcelName}</td>
                    <td className="text-surface-500 text-xs">{p.ParcelReference ?? "—"}</td>
                    <td className="text-right tabular-nums">
                      {p.AreaHectares ? parseFloat(p.AreaHectares).toFixed(2) : "—"}
                    </td>
                    <td>
                      {p.LandUseType
                        ? <span className="badge badge-slate text-xs">{p.LandUseType}</span>
                        : <span className="text-surface-400 text-xs">—</span>}
                    </td>
                    <td className="text-surface-500 text-xs">{p.Tenure ?? "—"}</td>
                    <td className="text-surface-500 text-xs">{p.PlanningReference ?? "—"}</td>
                    <td>
                      {p.BoundaryGeoJSON
                        ? <span className="badge badge-green text-xs">Mapped</span>
                        : <span className="text-surface-400 text-xs">None</span>}
                    </td>
                    <td className="text-right">
                      <button
                        className="btn-ghost btn-sm text-xs text-red-500 hover:text-red-700"
                        onClick={() => { if (confirm(`Delete "${p.ParcelName}"?`)) softDelete.mutate(p.LandParcelId); }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {showCreate && activeEntityId && (
        <CreateParcelModal entityId={activeEntityId} onClose={() => setShowCreate(false)} />
      )}
    </div>
  );
}

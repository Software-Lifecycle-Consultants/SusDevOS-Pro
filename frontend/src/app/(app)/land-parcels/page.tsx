"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Map, List, X } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { EmptyState } from "@/components/EmptyState";

// Leaflet requires no SSR
const LandMap = dynamic(() => import("@/components/land/LandMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[520px] rounded-xl border border-surface-200 bg-surface-50 flex items-center justify-center text-sm text-surface-400">
      Loading map…
    </div>
  ),
});

interface LandParcel {
  LandParcelId:    number;
  ParcelName:      string;
  ParcelReference: string | null;
  AreaHectares:    string | null;
  LandUseType:     string | null;
  Tenure:          string | null;
  PlanningReference: string | null;
  BoundaryGeoJSON: object | null;
  Status:          number;
}

const LAND_USE_TYPES = [
  "Greenfield", "Brownfield", "Agricultural", "Woodland",
  "Grassland", "Wetland", "Urban", "Mixed", "Other",
];

const TENURES = ["Freehold", "Leasehold", "Licensed", "Other"];

function CreateParcelModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    ParcelName: "", ParcelReference: "", AreaHectares: "",
    LandUseType: "", Tenure: "", PlanningReference: "", Description: "",
    BoundaryGeoJSON: "",
  });
  const [geoError, setGeoError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => {
      let boundary: object | null = null;
      if (form.BoundaryGeoJSON.trim()) {
        try { boundary = JSON.parse(form.BoundaryGeoJSON); }
        catch { throw new Error("Invalid GeoJSON"); }
      }
      return axiosInstance.post("/api/land-parcels/", {
        ParcelName:       form.ParcelName,
        ParcelReference:  form.ParcelReference  || null,
        AreaHectares:     form.AreaHectares      ? Number(form.AreaHectares) : null,
        LandUseType:      form.LandUseType       || null,
        Tenure:           form.Tenure            || null,
        PlanningReference:form.PlanningReference || null,
        Description:      form.Description       || null,
        BoundaryGeoJSON:  boundary,
      }, { headers });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["land-parcels", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      if (err instanceof Error && err.message === "Invalid GeoJSON") {
        setGeoError("Invalid GeoJSON. Paste a valid GeoJSON Polygon or MultiPolygon.");
        return;
      }
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to create parcel.");
    },
  });

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
    if (k === "BoundaryGeoJSON") setGeoError(null);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-surface-900">New land parcel</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div>
            <label className="label mb-1">Parcel name</label>
            <input className="input" required value={form.ParcelName}
              onChange={(e) => set("ParcelName", e.target.value)}
              placeholder="e.g. Site A — Development footprint" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Reference <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" value={form.ParcelReference}
                onChange={(e) => set("ParcelReference", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Area (ha)</label>
              <input className="input" type="number" step="any" min="0"
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
            <label className="label mb-1">Planning reference <span className="font-normal text-surface-400">optional</span></label>
            <input className="input" placeholder="e.g. 22/01234/FUL"
              value={form.PlanningReference} onChange={(e) => set("PlanningReference", e.target.value)} />
          </div>
          <div>
            <label className="label mb-1">
              Boundary GeoJSON{" "}
              <span className="font-normal text-surface-400">optional — paste a Polygon or MultiPolygon</span>
            </label>
            <textarea
              className={`input font-mono text-xs resize-y min-h-[90px] ${geoError ? "border-red-400" : ""}`}
              placeholder='{"type":"Polygon","coordinates":[[[...]]]}' rows={4}
              value={form.BoundaryGeoJSON} onChange={(e) => set("BoundaryGeoJSON", e.target.value)}
            />
            {geoError && <p className="mt-1 text-xs text-red-600">{geoError}</p>}
            <p className="mt-1 text-xs text-surface-400">
              Use QGIS, geojson.io, or export from OS Maps. Polygon drawing UI is available on Professional plan.
            </p>
          </div>
          <div>
            <label className="label mb-1">Description <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[60px]" rows={2}
              value={form.Description} onChange={(e) => set("Description", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save parcel"}
            </button>
          </div>
        </form>
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Land Parcels</h1>
          <p className="page-subtitle">{parcels.length} parcel{parcels.length !== 1 ? "s" : ""}</p>
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
                    <td>{p.LandUseType
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

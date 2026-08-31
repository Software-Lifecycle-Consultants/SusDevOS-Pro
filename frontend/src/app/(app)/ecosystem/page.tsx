"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { EmptyState } from "@/components/EmptyState";

interface Ecosystem {
  EcosystemId:   number;
  EcosystemName: string;
  EcosystemType: string;
  AreaHectares:  string | null;
  Description:   string;
  Status:        number;
}

interface Species {
  SpeciesId:      number;
  CommonName:     string;
  ScientificName: string;
  Family:         string;
  Kingdom:        string;
  IUCNStatus:     string;
  GBIFKey:        number | null;
  Status:         number;
}

const ECOSYSTEM_TYPES = [
  "Ancient Woodland","Semi-natural Woodland","Plantation Woodland",
  "Lowland Meadow","Upland Meadow","Calcareous Grassland",
  "Wetland","Bog","Heathland","Coastal","Riparian","Urban Green","Other",
];

const IUCN_COLOURS: Record<string, string> = {
  EX: "bg-black text-white",
  EW: "bg-gray-800 text-white",
  CR: "bg-red-600 text-white",
  EN: "bg-orange-500 text-white",
  VU: "bg-amber-400 text-surface-900",
  NT: "bg-blue-400 text-white",
  LC: "bg-brand-500 text-white",
  DD: "bg-surface-400 text-white",
  NE: "bg-surface-200 text-surface-600",
};

const IUCN_LABELS: Record<string, string> = {
  EX: "Extinct", EW: "Extinct in Wild",
  CR: "Critically Endangered", EN: "Endangered", VU: "Vulnerable",
  NT: "Near Threatened", LC: "Least Concern",
  DD: "Data Deficient", NE: "Not Evaluated",
};

function IUCNBadge({ status }: { status: string | null }) {
  if (!status) return <span className="text-surface-400 text-xs">—</span>;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-bold ${IUCN_COLOURS[status] ?? "bg-surface-200 text-surface-600"}`}
      title={IUCN_LABELS[status] ?? status}
    >
      {status}
    </span>
  );
}

function CreateEcosystemModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ EcosystemName: "", EcosystemType: "", AreaHectares: "", Description: "" });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => axiosInstance.post("/api/ecosystems/", {
      EcosystemName: form.EcosystemName,
      EcosystemType: form.EcosystemType,
      AreaHectares:  form.AreaHectares ? Number(form.AreaHectares) : null,
      Description:   form.Description,
    }, { headers }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["ecosystems", entityId] }); onClose(); },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to save.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold">New ecosystem / habitat</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div>
            <label className="label mb-1">Name</label>
            <input className="input" required placeholder="e.g. Ancient Semi-natural Woodland — North field"
              value={form.EcosystemName} onChange={(e) => set("EcosystemName", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Habitat type</label>
              <select className="input" value={form.EcosystemType} onChange={(e) => set("EcosystemType", e.target.value)}>
                <option value="">— select —</option>
                {ECOSYSTEM_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label mb-1">Area (ha)</label>
              <input className="input" type="number" step="any" min="0"
                value={form.AreaHectares} onChange={(e) => set("AreaHectares", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label mb-1">Description <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[70px]" rows={2}
              value={form.Description} onChange={(e) => set("Description", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save habitat"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CreateSpeciesModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    CommonName: "", ScientificName: "", Family: "", Kingdom: "Animalia",
    IUCNStatus: "", GBIFKey: "", Description: "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => axiosInstance.post("/api/species/", {
      CommonName:     form.CommonName,
      ScientificName: form.ScientificName,
      Family:         form.Family,
      Kingdom:        form.Kingdom,
      IUCNStatus:     form.IUCNStatus,
      GBIFKey:        form.GBIFKey ? Number(form.GBIFKey) : null,
      Description:    form.Description,
    }, { headers }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["species", entityId] }); onClose(); },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to save.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold">Record a species</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Common name</label>
              <input className="input" required placeholder="Barn owl"
                value={form.CommonName} onChange={(e) => set("CommonName", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Scientific name</label>
              <input className="input italic" placeholder="Tyto alba"
                value={form.ScientificName} onChange={(e) => set("ScientificName", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Family</label>
              <input className="input" placeholder="Tytonidae"
                value={form.Family} onChange={(e) => set("Family", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Kingdom</label>
              <select className="input" value={form.Kingdom} onChange={(e) => set("Kingdom", e.target.value)}>
                {["Animalia","Plantae","Fungi","Protista","Chromista"].map((k) => <option key={k}>{k}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">IUCN status</label>
              <select className="input" value={form.IUCNStatus} onChange={(e) => set("IUCNStatus", e.target.value)}>
                <option value="">— unknown —</option>
                {Object.entries(IUCN_LABELS).map(([code, label]) => (
                  <option key={code} value={code}>{code} — {label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label mb-1">GBIF key <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" type="number" placeholder="2498252"
                value={form.GBIFKey} onChange={(e) => set("GBIFKey", e.target.value)} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save species"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function EcosystemPage() {
  const { activeEntityId } = useAuthStore();
  const [tab, setTab] = useState<"habitats" | "species">("habitats");
  const [showCreateEco, setShowCreateEco] = useState(false);
  const [showCreateSp,  setShowCreateSp]  = useState(false);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const ecosystems = useQuery<{ results: Ecosystem[] }>({
    queryKey: ["ecosystems", activeEntityId],
    queryFn: () => axiosInstance.get("/api/ecosystems/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const species = useQuery<{ results: Species[] }>({
    queryKey: ["species", activeEntityId],
    queryFn: () => axiosInstance.get("/api/species/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const ecos = (ecosystems.data?.results ?? []).filter((e) => e.Status < 4);
  const specs = (species.data?.results ?? []).filter((s) => s.Status < 4);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Ecosystem & Species</h1>
          <p className="page-subtitle">Pre-development baseline and habitat records.</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => tab === "habitats" ? setShowCreateEco(true) : setShowCreateSp(true)}
        >
          <Plus className="h-4 w-4" />
          {tab === "habitats" ? "New habitat" : "Record species"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-surface-200">
        {(["habitats", "species"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={[
              "px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors capitalize",
              tab === t
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-surface-500 hover:text-surface-800",
            ].join(" ")}
          >
            {t} {t === "habitats" ? `(${ecos.length})` : `(${specs.length})`}
          </button>
        ))}
      </div>

      {/* Habitats */}
      {tab === "habitats" && (
        <div className="card overflow-hidden">
          {ecosystems.isLoading ? (
            <div className="p-6 text-sm text-surface-500">Loading…</div>
          ) : ecos.length === 0 ? (
            <EmptyState message="No habitat records yet." />
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Habitat name</th>
                  <th>Type</th>
                  <th className="text-right">Area (ha)</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {ecos.map((e) => (
                  <tr key={e.EcosystemId}>
                    <td className="font-medium">
                      <Link href={`/ecosystem/${e.EcosystemId}`} className="text-brand-700 hover:underline">{e.EcosystemName}</Link>
                    </td>
                    <td>{e.EcosystemType
                      ? <span className="badge badge-slate text-xs">{e.EcosystemType}</span>
                      : <span className="text-surface-400 text-xs">—</span>}
                    </td>
                    <td className="text-right tabular-nums">
                      {e.AreaHectares ? parseFloat(e.AreaHectares).toFixed(2) : "—"}
                    </td>
                    <td className="text-surface-500 text-xs truncate max-w-[240px]">{e.Description || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Species */}
      {tab === "species" && (
        <div className="card overflow-hidden">
          {species.isLoading ? (
            <div className="p-6 text-sm text-surface-500">Loading…</div>
          ) : specs.length === 0 ? (
            <EmptyState message="No species recorded yet." />
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Common name</th>
                  <th>Scientific name</th>
                  <th>Family</th>
                  <th>Kingdom</th>
                  <th>IUCN status</th>
                  <th>GBIF key</th>
                </tr>
              </thead>
              <tbody>
                {specs.map((s) => (
                  <tr key={s.SpeciesId}>
                    <td className="font-medium">
                      <Link href={`/species/${s.SpeciesId}`} className="text-brand-700 hover:underline">{s.CommonName}</Link>
                    </td>
                    <td className="italic text-surface-600 text-sm">{s.ScientificName || "—"}</td>
                    <td className="text-surface-500 text-sm">{s.Family || "—"}</td>
                    <td className="text-surface-500 text-sm">{s.Kingdom || "—"}</td>
                    <td><IUCNBadge status={s.IUCNStatus} /></td>
                    <td className="text-surface-400 text-xs">
                      {s.GBIFKey
                        ? <a href={`https://www.gbif.org/species/${s.GBIFKey}`} target="_blank"
                            rel="noopener noreferrer" className="text-brand-600 hover:underline">
                            {s.GBIFKey}
                          </a>
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {showCreateEco && activeEntityId && (
        <CreateEcosystemModal entityId={activeEntityId} onClose={() => setShowCreateEco(false)} />
      )}
      {showCreateSp && activeEntityId && (
        <CreateSpeciesModal entityId={activeEntityId} onClose={() => setShowCreateSp(false)} />
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, TreePine, Sprout } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { EmptyState } from "@/components/EmptyState";

interface TreeRemoval {
  TreeRemovalId:     number;
  RemovalReference:  string | null;
  RemovalDate:       string | null;
  TotalTreesRemoved: number | null;
  TotalBiomassCarbon: string | null;
  HasMitigationPlan:  boolean;
  Description:       string | null;
  Status:            number;
}

interface Restoration {
  RestorationId:    number;
  RestorationName:  string;
  RestorationReference: string | null;
  StartDate:        string | null;
  CompletionDate:   string | null;
  TotalAreaHectares: string | null;
  TotalTreesPlanted: number | null;
  EstimatedCarbonSequestrationTonnes: string | null;
  Status:           number;
}

function fmt(v: string | null, dp = 2) {
  return v ? parseFloat(v).toFixed(dp) : "—";
}

function CreateRemovalModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    RemovalReference: "", Description: "", RemovalDate: "",
    TotalTreesRemoved: "", TotalBiomassCarbon: "",
    HasMitigationPlan: "false", MitigationNotes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => axiosInstance.post("/api/tree-removals/", {
      RemovalReference:  form.RemovalReference  || null,
      Description:       form.Description       || null,
      RemovalDate:       form.RemovalDate        || null,
      TotalTreesRemoved: form.TotalTreesRemoved  ? Number(form.TotalTreesRemoved)  : null,
      TotalBiomassCarbon:form.TotalBiomassCarbon ? Number(form.TotalBiomassCarbon) : null,
      HasMitigationPlan: form.HasMitigationPlan === "true",
      MitigationNotes:   form.MitigationNotes   || null,
    }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tree-removals", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to save.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold">New tree removal record</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Reference <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" placeholder="e.g. AIA-2024-01"
                value={form.RemovalReference} onChange={(e) => set("RemovalReference", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Removal date</label>
              <input className="input" type="date"
                value={form.RemovalDate} onChange={(e) => set("RemovalDate", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Total trees removed</label>
              <input className="input" type="number" min="0"
                value={form.TotalTreesRemoved} onChange={(e) => set("TotalTreesRemoved", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Biomass carbon (tCO₂e)</label>
              <input className="input" type="number" step="any" min="0"
                value={form.TotalBiomassCarbon} onChange={(e) => set("TotalBiomassCarbon", e.target.value)} />
              <p className="mt-1 text-xs text-surface-400">From arboricultural survey or IPCC Tier 1 calc</p>
            </div>
          </div>
          <div>
            <label className="label mb-1">Mitigation plan</label>
            <select className="input" value={form.HasMitigationPlan}
              onChange={(e) => set("HasMitigationPlan", e.target.value)}>
              <option value="false">No mitigation plan</option>
              <option value="true">Yes — mitigation plan in place</option>
            </select>
          </div>
          {form.HasMitigationPlan === "true" && (
            <div>
              <label className="label mb-1">Mitigation notes</label>
              <textarea className="input resize-y min-h-[70px]" rows={2}
                value={form.MitigationNotes} onChange={(e) => set("MitigationNotes", e.target.value)} />
            </div>
          )}
          <div>
            <label className="label mb-1">Description <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[60px]" rows={2}
              value={form.Description} onChange={(e) => set("Description", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save record"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function CreateRestorationModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    RestorationName: "", RestorationReference: "", Description: "",
    StartDate: "", CompletionDate: "", TotalAreaHectares: "",
    TotalTreesPlanted: "", EstimatedCarbonSequestrationTonnes: "", MonitoringNotes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => axiosInstance.post("/api/restorations/", {
      RestorationName:      form.RestorationName,
      RestorationReference: form.RestorationReference || null,
      Description:          form.Description          || null,
      StartDate:            form.StartDate             || null,
      CompletionDate:       form.CompletionDate        || null,
      TotalAreaHectares:    form.TotalAreaHectares     ? Number(form.TotalAreaHectares)    : null,
      TotalTreesPlanted:    form.TotalTreesPlanted     ? Number(form.TotalTreesPlanted)    : null,
      EstimatedCarbonSequestrationTonnes:
        form.EstimatedCarbonSequestrationTonnes
          ? Number(form.EstimatedCarbonSequestrationTonnes) : null,
      MonitoringNotes:      form.MonitoringNotes       || null,
    }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["restorations", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to save.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold">New restoration</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div>
            <label className="label mb-1">Restoration name</label>
            <input className="input" required placeholder="e.g. Receptor woodland — eastern buffer"
              value={form.RestorationName} onChange={(e) => set("RestorationName", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Reference <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" value={form.RestorationReference}
                onChange={(e) => set("RestorationReference", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Area (ha)</label>
              <input className="input" type="number" step="any" min="0"
                value={form.TotalAreaHectares} onChange={(e) => set("TotalAreaHectares", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Start date</label>
              <input className="input" type="date"
                value={form.StartDate} onChange={(e) => set("StartDate", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Completion date <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" type="date"
                value={form.CompletionDate} onChange={(e) => set("CompletionDate", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Trees planted</label>
              <input className="input" type="number" min="0"
                value={form.TotalTreesPlanted} onChange={(e) => set("TotalTreesPlanted", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Est. sequestration (tCO₂e)</label>
              <input className="input" type="number" step="any" min="0"
                value={form.EstimatedCarbonSequestrationTonnes}
                onChange={(e) => set("EstimatedCarbonSequestrationTonnes", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label mb-1">Monitoring notes <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[60px]" rows={2}
              value={form.MonitoringNotes} onChange={(e) => set("MonitoringNotes", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save restoration"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function RestorationsPage() {
  const { activeEntityId } = useAuthStore();
  const [tab, setTab] = useState<"removals" | "restorations">("removals");
  const [showCreateRemoval, setShowCreateRemoval] = useState(false);
  const [showCreateRestoration, setShowCreateRestoration] = useState(false);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const removals = useQuery<{ results: TreeRemoval[] }>({
    queryKey: ["tree-removals", activeEntityId],
    queryFn: () => axiosInstance.get("/api/tree-removals/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const restorations = useQuery<{ results: Restoration[] }>({
    queryKey: ["restorations", activeEntityId],
    queryFn: () => axiosInstance.get("/api/restorations/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const rems  = (removals.data?.results     ?? []).filter((r) => r.Status < 4);
  const rests = (restorations.data?.results ?? []).filter((r) => r.Status < 4);

  const totalRemoved = rems.reduce((a, r) => a + (r.TotalTreesRemoved ?? 0), 0);
  const totalBiomass = rems.reduce((a, r) => a + parseFloat(r.TotalBiomassCarbon ?? "0"), 0);
  const totalPlanted = rests.reduce((a, r) => a + (r.TotalTreesPlanted ?? 0), 0);
  const totalSeq     = rests.reduce((a, r) => a + parseFloat(r.EstimatedCarbonSequestrationTonnes ?? "0"), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Restorations</h1>
          <p className="page-subtitle">Tree removals and habitat restoration tracking.</p>
        </div>
        <button
          className="btn-primary flex items-center gap-2"
          onClick={() => tab === "removals" ? setShowCreateRemoval(true) : setShowCreateRestoration(true)}
        >
          <Plus className="h-4 w-4" />
          {tab === "removals" ? "New removal" : "New restoration"}
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="card p-4 flex items-center gap-3">
          <TreePine className="h-8 w-8 text-red-400 shrink-0" />
          <div>
            <p className="text-xs text-surface-500">Trees removed</p>
            <p className="text-xl font-semibold text-surface-900">{totalRemoved.toLocaleString()}</p>
          </div>
        </div>
        <div className="card p-4">
          <p className="text-xs text-surface-500">Biomass carbon lost</p>
          <p className="text-xl font-semibold text-red-600">{totalBiomass.toFixed(2)} tCO₂e</p>
        </div>
        <div className="card p-4 flex items-center gap-3">
          <Sprout className="h-8 w-8 text-brand-500 shrink-0" />
          <div>
            <p className="text-xs text-surface-500">Trees planted</p>
            <p className="text-xl font-semibold text-surface-900">{totalPlanted.toLocaleString()}</p>
          </div>
        </div>
        <div className="card p-4">
          <p className="text-xs text-surface-500">Est. sequestration</p>
          <p className="text-xl font-semibold text-brand-700">{totalSeq.toFixed(2)} tCO₂e</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-surface-200">
        {(["removals", "restorations"] as const).map((t) => (
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
            {t === "removals" ? `Tree Removals (${rems.length})` : `Restorations (${rests.length})`}
          </button>
        ))}
      </div>

      {/* Tree removals table */}
      {tab === "removals" && (
        <div className="card overflow-hidden">
          {removals.isLoading ? (
            <div className="p-6 text-sm text-surface-500">Loading…</div>
          ) : rems.length === 0 ? (
            <EmptyState message="No tree removal records yet." />
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Date</th>
                  <th className="text-right">Trees</th>
                  <th className="text-right">Biomass (tCO₂e)</th>
                  <th>Mitigation</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {rems.map((r) => (
                  <tr key={r.TreeRemovalId}>
                    <td className="font-medium">
                      <Link href={`/tree-removals/${r.TreeRemovalId}`} className="text-brand-700 hover:underline">
                        {r.RemovalReference ?? `#${r.TreeRemovalId}`}
                      </Link>
                    </td>
                    <td className="text-surface-500 text-sm">
                      {r.RemovalDate ? new Date(r.RemovalDate).toLocaleDateString() : "—"}
                    </td>
                    <td className="text-right tabular-nums font-medium">
                      {r.TotalTreesRemoved?.toLocaleString() ?? "—"}
                    </td>
                    <td className="text-right tabular-nums text-red-600 font-medium">
                      {fmt(r.TotalBiomassCarbon)}
                    </td>
                    <td>
                      {r.HasMitigationPlan
                        ? <span className="badge badge-green text-xs">Plan in place</span>
                        : <span className="badge badge-red text-xs">None</span>}
                    </td>
                    <td className="text-surface-500 text-xs truncate max-w-[200px]">{r.Description ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Restorations table */}
      {tab === "restorations" && (
        <div className="card overflow-hidden">
          {restorations.isLoading ? (
            <div className="p-6 text-sm text-surface-500">Loading…</div>
          ) : rests.length === 0 ? (
            <EmptyState message="No restoration records yet." />
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Start date</th>
                  <th className="text-right">Area (ha)</th>
                  <th className="text-right">Trees planted</th>
                  <th className="text-right">Est. sequestration (t)</th>
                  <th>Completion</th>
                </tr>
              </thead>
              <tbody>
                {rests.map((r) => (
                  <tr key={r.RestorationId}>
                    <td className="font-medium">
                      <Link href={`/restorations/${r.RestorationId}`} className="text-brand-700 hover:underline">{r.RestorationName}</Link>
                    </td>
                    <td className="text-surface-500 text-sm">
                      {r.StartDate ? new Date(r.StartDate).toLocaleDateString() : "—"}
                    </td>
                    <td className="text-right tabular-nums">{fmt(r.TotalAreaHectares)}</td>
                    <td className="text-right tabular-nums font-medium text-brand-700">
                      {r.TotalTreesPlanted?.toLocaleString() ?? "—"}
                    </td>
                    <td className="text-right tabular-nums font-medium text-brand-700">
                      {fmt(r.EstimatedCarbonSequestrationTonnes)}
                    </td>
                    <td className="text-surface-500 text-sm">
                      {r.CompletionDate ? new Date(r.CompletionDate).toLocaleDateString() : "In progress"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {showCreateRemoval && activeEntityId && (
        <CreateRemovalModal entityId={activeEntityId} onClose={() => setShowCreateRemoval(false)} />
      )}
      {showCreateRestoration && activeEntityId && (
        <CreateRestorationModal entityId={activeEntityId} onClose={() => setShowCreateRestoration(false)} />
      )}
    </div>
  );
}

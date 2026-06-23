"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, ChevronRight, Lock, Unlock } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface GHGInventory {
  InventoryId:               number;
  ReportingYear:             number;
  BaseYear:                  number | null;
  ConsolidationApproach:     number | null;
  VerificationStatus:        number;
  BoundaryNotes:             string | null;
  TotalScope1Tonnes:         string | null;
  TotalScope2LocationTonnes: string | null;
  TotalScope2MarketTonnes:   string | null;
  TotalScope3Tonnes:         string | null;
  NetEmissionsTonnes:        string | null;
  VerifiedBy:                string | null;
  VerifiedAt:                string | null;
}

const VERIF_STATUS: Record<number, { label: string; badge: string; next?: string }> = {
  0: { label: "Draft",               badge: "badge-slate",  next: "Submit for review"   },
  1: { label: "Submitted",           badge: "badge-yellow", next: "Internally approve"  },
  2: { label: "Internally approved", badge: "badge-blue",   next: "Mark third-party verified" },
  3: { label: "Verified",            badge: "badge-green"                               },
  4: { label: "Rejected",            badge: "badge-red",    next: "Reset to draft"      },
  5: { label: "CDP Submitted",       badge: "badge-blue"                                },
};

const CONSOLIDATION_LABELS: Record<number, string> = {
  1: "Equity Share",
  2: "Financial Control",
  3: "Operational Control",
};

function fmt(val: string | null) {
  if (!val) return "—";
  return parseFloat(val).toFixed(2);
}

function CreateInventoryModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    ReportingYear:         String(new Date().getFullYear()),
    BaseYear:              "",
    ConsolidationApproach: "2",
    BoundaryNotes:         "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () =>
      axiosInstance.post("/api/ghg-inventories/", {
        ReportingYear:         Number(form.ReportingYear),
        BaseYear:              form.BaseYear ? Number(form.BaseYear) : null,
        ConsolidationApproach: form.ConsolidationApproach ? Number(form.ConsolidationApproach) : null,
        BoundaryNotes:         form.BoundaryNotes || null,
      }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventories", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = data ? Object.values(data)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to create inventory.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-surface-900">New GHG inventory</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Reporting year</label>
              <input className="input" type="number" min={2000} max={2100} required
                value={form.ReportingYear} onChange={(e) => set("ReportingYear", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Base year <span className="font-normal text-surface-400">(SBTi)</span></label>
              <input className="input" type="number" min={2000} max={2100}
                value={form.BaseYear} onChange={(e) => set("BaseYear", e.target.value)}
                placeholder="e.g. 2019" />
            </div>
          </div>

          <div>
            <label className="label mb-1">Consolidation approach</label>
            <select className="input" value={form.ConsolidationApproach}
              onChange={(e) => set("ConsolidationApproach", e.target.value)}>
              <option value="1">Equity Share</option>
              <option value="2">Financial Control</option>
              <option value="3">Operational Control</option>
            </select>
          </div>

          <div>
            <label className="label mb-1">Boundary notes <span className="font-normal text-surface-400">(optional)</span></label>
            <textarea className="input min-h-[80px] resize-y" rows={3}
              placeholder="Describe what is included / excluded from this inventory boundary…"
              value={form.BoundaryNotes} onChange={(e) => set("BoundaryNotes", e.target.value)} />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Creating…" : "Create inventory"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function InventoriesPage() {
  const { activeEntityId, user } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [unlockReason, setUnlockReason] = useState<{ id: number; reason: string } | null>(null);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: GHGInventory[] }>({
    queryKey: ["inventories", activeEntityId],
    queryFn: () => axiosInstance.get("/api/ghg-inventories/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const advance = useMutation({
    mutationFn: ({ id, newStatus }: { id: number; newStatus: number }) =>
      axiosInstance.patch(`/api/ghg-inventories/${id}/`, { VerificationStatus: newStatus }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inventories", activeEntityId] }),
  });

  const unlock = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      axiosInstance.post(`/api/ghg-inventories/${id}/unlock/`, { reason }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventories", activeEntityId] });
      setUnlockReason(null);
    },
  });

  const inventories = data?.results ?? [];
  const isSA = user?.IsSuperAdmin;

  function nextStatus(current: number) {
    if (current === 0) return 1;
    if (current === 1) return 2;
    if (current === 2) return 3;
    if (current === 4) return 0;
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">GHG Inventories</h1>
          <p className="page-subtitle">Formal annual inventories with verification workflow.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> New inventory
        </button>
      </div>

      {/* Workflow guide */}
      <div className="rounded-lg border border-surface-200 bg-surface-50 px-4 py-3 flex items-center gap-3 text-xs text-surface-500">
        {["Draft","Submitted","Internally approved","Verified"].map((s, i, arr) => (
          <span key={s} className="flex items-center gap-2">
            <span className={i === 0 ? "text-surface-700 font-medium" : ""}>{s}</span>
            {i < arr.length - 1 && <ChevronRight className="h-3 w-3 text-surface-300" />}
          </span>
        ))}
        <span className="ml-auto text-surface-400">
          Verified inventories are immutable (SuperAdmin unlock required)
        </span>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : inventories.length === 0 ? (
          <div className="p-6 text-sm text-surface-500">
            No inventories yet.{" "}
            <button className="text-brand-600 hover:underline" onClick={() => setShowCreate(true)}>
              Create your first inventory →
            </button>
          </div>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Year</th>
                <th>Base year</th>
                <th>Approach</th>
                <th className="text-right">Sc.1 (t)</th>
                <th className="text-right">Sc.2 Loc (t)</th>
                <th className="text-right">Sc.3 (t)</th>
                <th className="text-right">Net (t)</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {inventories.map((inv) => {
                const vs = VERIF_STATUS[inv.VerificationStatus] ?? VERIF_STATUS[0];
                const next = nextStatus(inv.VerificationStatus);
                const isLocked = inv.VerificationStatus >= 3;

                return (
                  <tr key={inv.InventoryId}>
                    <td className="font-semibold text-surface-800">{inv.ReportingYear}</td>
                    <td className="text-surface-500">{inv.BaseYear ?? "—"}</td>
                    <td className="text-surface-500 text-xs">
                      {inv.ConsolidationApproach
                        ? CONSOLIDATION_LABELS[inv.ConsolidationApproach]
                        : "—"}
                    </td>
                    <td className="text-right tabular-nums">{fmt(inv.TotalScope1Tonnes)}</td>
                    <td className="text-right tabular-nums">{fmt(inv.TotalScope2LocationTonnes)}</td>
                    <td className="text-right tabular-nums">{fmt(inv.TotalScope3Tonnes)}</td>
                    <td className="text-right tabular-nums font-medium">{fmt(inv.NetEmissionsTonnes)}</td>
                    <td>
                      <span className={`badge ${vs.badge}`}>{vs.label}</span>
                    </td>
                    <td className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* Advance workflow */}
                        {!isLocked && next !== null && vs.next && (
                          <button
                            className="btn-secondary btn-sm text-xs"
                            disabled={advance.isPending}
                            onClick={() => advance.mutate({ id: inv.InventoryId, newStatus: next })}
                          >
                            {vs.next}
                          </button>
                        )}
                        {/* Lock indicator */}
                        {isLocked && (
                          <span title="Verified — immutable">
                            <Lock className="h-3.5 w-3.5 text-surface-400" />
                          </span>
                        )}
                        {/* SA unlock */}
                        {isLocked && isSA && (
                          <button
                            className="btn-ghost btn-sm text-xs text-amber-600"
                            onClick={() => setUnlockReason({ id: inv.InventoryId, reason: "" })}
                            title="Unlock (SuperAdmin)"
                          >
                            <Unlock className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Unlock modal */}
      {unlockReason && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="card w-full max-w-sm p-6">
            <h2 className="text-base font-semibold text-surface-900 mb-1">Unlock verified inventory</h2>
            <p className="text-sm text-surface-500 mb-4">
              This action is audited. Provide a reason — it will be written to the audit log.
            </p>
            <textarea
              className="input min-h-[80px] resize-y mb-4"
              placeholder="Reason for unlocking…"
              value={unlockReason.reason}
              onChange={(e) => setUnlockReason((u) => u ? { ...u, reason: e.target.value } : u)}
            />
            <div className="flex justify-end gap-2">
              <button className="btn-secondary" onClick={() => setUnlockReason(null)}>Cancel</button>
              <button
                className="btn-danger"
                disabled={!unlockReason.reason.trim() || unlock.isPending}
                onClick={() => unlock.mutate(unlockReason)}
              >
                {unlock.isPending ? "Unlocking…" : "Unlock inventory"}
              </button>
            </div>
          </div>
        </div>
      )}

      {showCreate && activeEntityId && (
        <CreateInventoryModal entityId={activeEntityId} onClose={() => setShowCreate(false)} />
      )}
    </div>
  );
}

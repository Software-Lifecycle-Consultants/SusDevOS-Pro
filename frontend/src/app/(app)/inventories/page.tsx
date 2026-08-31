"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, ChevronRight, Lock, Unlock } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface GHGInventory {
  InventoryId:               number;
  ReportingYear:             number;
  ReportingPeriodFrom:       string;
  ReportingPeriodTo:         string;
  BaselineYear:              number | null;
  GwpDatasetName:            string;
  ConsolidationApproach:     number | null;
  VerificationStatus:        number;
  BoundaryNotes:             string;
  TotalScope1Tonnes:         string | null;
  TotalScope2LocationTonnes: string | null;
  TotalScope2MarketTonnes:   string | null;
  TotalScope3Tonnes:         string | null;
  NetEmissionsTonnes:        string | null;
  VerifiedBy:                string | null;
  VerifiedAt:                string | null;
}

interface ReconciliationRecord {
  EmissionsId: number;
  Title: string;
  Scope: number;
  ReportingPeriodFrom: string | null;
  ReportingPeriodTo: string | null;
}

interface ReconciliationResult {
  candidate_count: number;
  incomplete_count: number;
  candidates: ReconciliationRecord[];
  incomplete: ReconciliationRecord[];
}

const VERIF_STATUS: Record<number, { label: string; badge: string }> = {
  1: { label: "Unverified",             badge: "badge-slate" },
  2: { label: "Pending review",          badge: "badge-yellow" },
  3: { label: "Verified — first party",  badge: "badge-green" },
  4: { label: "Verified — third party",  badge: "badge-green" },
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
  const currentYear = new Date().getFullYear();
  const [form, setForm] = useState({
    ReportingYear:         String(currentYear),
    ReportingPeriodFrom:   `${currentYear}-01-01`,
    ReportingPeriodTo:     `${currentYear}-12-31`,
    BaselineYear:          "",
    ConsolidationApproach: "2",
    BoundaryNotes:         "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () =>
      axiosInstance.post("/api/ghg-inventories/", {
        ReportingYear:         Number(form.ReportingYear),
        ReportingPeriodFrom:   form.ReportingPeriodFrom,
        ReportingPeriodTo:     form.ReportingPeriodTo,
        BaselineYear:          form.BaselineYear ? Number(form.BaselineYear) : null,
        ConsolidationApproach: form.ConsolidationApproach ? Number(form.ConsolidationApproach) : null,
        BoundaryNotes:         form.BoundaryNotes,
      }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventories", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const errors = data?.errors as Record<string, unknown> | undefined;
      const first = errors ? Object.values(errors)[0] : null;
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
              <label className="label mb-1">Base year <span className="font-normal text-surface-400">(optional)</span></label>
              <input className="input" type="number" min={2000} max={2100}
                value={form.BaselineYear} onChange={(e) => set("BaselineYear", e.target.value)}
                placeholder="e.g. 2019" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="label">Reporting period</label>
              <button
                type="button"
                className="text-xs text-brand-600 hover:underline"
                onClick={() => {
                  const year = Number(form.ReportingYear) || currentYear;
                  setForm((f) => ({
                    ...f,
                    ReportingPeriodFrom: `${year}-01-01`,
                    ReportingPeriodTo: `${year}-12-31`,
                  }));
                }}
              >
                Use calendar year
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input className="input" type="date" required value={form.ReportingPeriodFrom}
                onChange={(e) => set("ReportingPeriodFrom", e.target.value)} />
              <input className="input" type="date" required value={form.ReportingPeriodTo}
                onChange={(e) => set("ReportingPeriodTo", e.target.value)} />
            </div>
            <p className="mt-1 text-xs text-surface-400">
              The active platform GWP dataset is recorded with the inventory.
            </p>
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
  const [reconciliationId, setReconciliationId] = useState<number | null>(null);
  const [verificationNotes, setVerificationNotes] = useState("");
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: GHGInventory[] }>({
    queryKey: ["inventories", activeEntityId],
    queryFn: () => axiosInstance.get("/api/ghg-inventories/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const { data: reconciliation, isLoading: reconciliationLoading } = useQuery<ReconciliationResult>({
    queryKey: ["inventory-reconciliation", reconciliationId, activeEntityId],
    queryFn: () =>
      axiosInstance
        .get(`/api/ghg-inventories/${reconciliationId}/unassigned-emissions/`, { headers })
        .then((response) => response.data),
    enabled: reconciliationId !== null && Boolean(activeEntityId),
  });

  function workflowErrorMessage(error: unknown) {
    const data = (
      error as { response?: { data?: { detail?: string; code?: string } } }
    )?.response?.data;
    return data?.detail ?? "Inventory workflow action failed.";
  }

  const submit = useMutation({
    mutationFn: ({ id, acknowledge = false }: { id: number; acknowledge?: boolean }) =>
      axiosInstance.post(
        `/api/ghg-inventories/${id}/submit/`,
        { acknowledge_unassigned: acknowledge },
        { headers },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventories", activeEntityId] });
      setReconciliationId(null);
      setWorkflowError(null);
    },
    onError: (error, variables) => {
      const code = (error as { response?: { data?: { code?: string } } })?.response?.data?.code;
      if (code === "unassigned_records_require_review") setReconciliationId(variables.id);
      setWorkflowError(workflowErrorMessage(error));
    },
  });

  const verify = useMutation({
    mutationFn: ({ id, notes, acknowledge = false }: { id: number; notes: string; acknowledge?: boolean }) =>
      axiosInstance.post(
        `/api/ghg-inventories/${id}/verify/`,
        { notes: notes || null, acknowledge_unassigned: acknowledge },
        { headers },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventories", activeEntityId] });
      setReconciliationId(null);
      setVerificationNotes("");
      setWorkflowError(null);
    },
    onError: (error, variables) => {
      const code = (error as { response?: { data?: { code?: string } } })?.response?.data?.code;
      if (code === "unassigned_records_require_review") setReconciliationId(variables.id);
      setWorkflowError(workflowErrorMessage(error));
    },
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
  const canVerify = Boolean(user?.IsSuperAdmin || user?.role === "admin");
  const reconciliationInventory = inventories.find(
    (inventory) => inventory.InventoryId === reconciliationId,
  );

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

      {workflowError && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {workflowError}
        </div>
      )}

      {/* Workflow guide */}
      <div className="rounded-lg border border-surface-200 bg-surface-50 px-4 py-3 flex items-center gap-3 text-xs text-surface-500">
        {["Unverified","Pending review","Verified & locked"].map((s, i, arr) => (
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
                const vs = VERIF_STATUS[inv.VerificationStatus] ?? VERIF_STATUS[1];
                const isLocked = inv.VerificationStatus >= 3;

                return (
                  <tr key={inv.InventoryId}>
                    <td className="font-semibold text-surface-800">{inv.ReportingYear}</td>
                    <td className="text-surface-500">{inv.BaselineYear ?? "—"}</td>
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
                        {!isLocked && (
                          <button
                            className="btn-ghost btn-sm text-xs"
                            onClick={() => {
                              setWorkflowError(null);
                              setReconciliationId(inv.InventoryId);
                            }}
                          >
                            Review data
                          </button>
                        )}
                        {inv.VerificationStatus === 1 && (
                          <button
                            className="btn-secondary btn-sm text-xs"
                            disabled={submit.isPending}
                            onClick={() => submit.mutate({ id: inv.InventoryId })}
                          >
                            Submit for review
                          </button>
                        )}
                        {inv.VerificationStatus === 2 && canVerify && (
                          <button
                            className="btn-secondary btn-sm text-xs"
                            disabled={verify.isPending}
                            onClick={() => {
                              const notes = window.prompt("Verification notes (optional):") ?? null;
                              if (notes !== null) {
                                setVerificationNotes(notes);
                                verify.mutate({ id: inv.InventoryId, notes });
                              }
                            }}
                          >
                            Verify &amp; lock
                          </button>
                        )}
                        {inv.VerificationStatus === 2 && !canVerify && (
                          <span className="text-xs text-surface-400">Awaiting entity admin</span>
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

      {reconciliationId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="card flex max-h-[85vh] w-full max-w-2xl flex-col p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-surface-900">
                  Review unassigned records
                </h2>
                <p className="mt-1 text-sm text-surface-500">
                  These records are not included in the {reconciliationInventory?.ReportingYear ?? "selected"} inventory totals.
                  Assign only those that belong inside this inventory boundary.
                </p>
              </div>
              <button
                className="btn-ghost btn-sm"
                onClick={() => {
                  setReconciliationId(null);
                  setWorkflowError(null);
                }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 flex-1 overflow-y-auto border-y border-surface-100 py-3">
              {reconciliationLoading ? (
                <p className="text-sm text-surface-500">Checking records…</p>
              ) : (reconciliation?.candidate_count ?? 0) + (reconciliation?.incomplete_count ?? 0) === 0 ? (
                <p className="text-sm text-surface-500">
                  No unassigned records match this reporting year and period.
                </p>
              ) : (
                <div className="space-y-4">
                  {(reconciliation?.candidates ?? []).length > 0 && (
                    <div>
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-surface-400">
                        Inside the reporting period
                      </h3>
                      <div className="mt-2 divide-y divide-surface-100 rounded border border-surface-200">
                        {reconciliation?.candidates.map((record) => (
                          <div key={record.EmissionsId} className="flex items-center justify-between gap-3 px-3 py-2">
                            <div>
                              <div className="text-sm font-medium text-surface-800">{record.Title}</div>
                              <div className="text-xs text-surface-400">
                                Scope {record.Scope} · {record.ReportingPeriodFrom} to {record.ReportingPeriodTo}
                              </div>
                            </div>
                            <Link className="text-sm text-brand-600 hover:underline" href={`/emissions/${record.EmissionsId}`}>
                              Review &amp; assign
                            </Link>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {(reconciliation?.incomplete ?? []).length > 0 && (
                    <div>
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-600">
                        Missing reporting dates
                      </h3>
                      <div className="mt-2 divide-y divide-surface-100 rounded border border-amber-200 bg-amber-50/40">
                        {reconciliation?.incomplete.map((record) => (
                          <div key={record.EmissionsId} className="flex items-center justify-between gap-3 px-3 py-2">
                            <div>
                              <div className="text-sm font-medium text-surface-800">{record.Title}</div>
                              <div className="text-xs text-amber-700">Scope {record.Scope} · reporting period incomplete</div>
                            </div>
                            <Link className="text-sm text-brand-600 hover:underline" href={`/emissions/${record.EmissionsId}`}>
                              Complete record
                            </Link>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="mt-4 flex items-center justify-between gap-3">
              <p className="max-w-md text-xs text-surface-400">
                Continuing acknowledges that remaining unassigned records were reviewed and are intentionally outside this inventory.
              </p>
              <div className="flex shrink-0 gap-2">
                <button className="btn-secondary" onClick={() => setReconciliationId(null)}>
                  Close
                </button>
                {reconciliationInventory?.VerificationStatus === 1 && (
                  <button
                    className="btn-primary"
                    disabled={submit.isPending || reconciliationLoading}
                    onClick={() => submit.mutate({ id: reconciliationId, acknowledge: true })}
                  >
                    Submit after review
                  </button>
                )}
                {reconciliationInventory?.VerificationStatus === 2 && canVerify && (
                  <button
                    className="btn-primary"
                    disabled={verify.isPending || reconciliationLoading}
                    onClick={() =>
                      verify.mutate({
                        id: reconciliationId,
                        notes: verificationNotes,
                        acknowledge: true,
                      })
                    }
                  >
                    Verify after review
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

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

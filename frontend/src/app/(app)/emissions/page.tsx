"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";
import { EmptyState } from "@/components/EmptyState";
import { EFPicker, type EmissionFactor } from "@/components/emissions/EFPicker";

interface EmissionsRecord {
  EmissionsId:           number;
  Title:                 string;
  Scope:                 number;
  Scope3Category:        number | null;
  Gas:                   string;
  EmissionsAmountTonnes: string | null;
  VerificationStatus:    number;
  ReportingYear:         number | null;
  Status:                number;
  CreatedAt:             string;
}

interface Project {
  ProjectId:   number;
  ProjectName: string;
}

interface ProjectPhase {
  PhaseId: number;
  PhaseName: string;
  PhaseNumber: number | null;
}

interface Inventory {
  InventoryId: number;
  ReportingYear: number;
  ReportingPeriodFrom: string;
  ReportingPeriodTo: string;
  VerificationStatus: number;
}

const SCOPE_LABELS: Record<number, string> = { 1: "Scope 1", 2: "Scope 2", 3: "Scope 3" };
const VERIF_LABELS: Record<number, { label: string; cls: string }> = {
  1: { label: "Unverified", cls: "badge-slate" },
  2: { label: "Pending",    cls: "badge-yellow" },
  3: { label: "Verified",   cls: "badge-green" },
  4: { label: "3rd Party",  cls: "badge-green" },
};

interface CreateEmissionPayload {
  Title: string;
  Scope: number;
  QuantityOrCost: string;
  Unit: string;
  EmissionFactor: string;
  EmissionFactorSource: string;
  EmissionFactorId: number;
  Gas: string;
  GasSubtype: string | null;
  Scope3Category: number | null;
  ReportingPeriodFrom: string;
  ReportingPeriodTo: string;
  ReportingYear: number;
  ProjectId: number | null;
  PhaseId: number | null;
  InventoryId: number | null;
  SupplierName: string | null;
  ActivityDescription: string | null;
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2 pb-1 mb-3 border-b border-surface-100">
      <span className="text-xs font-semibold uppercase tracking-wider text-surface-400">{children}</span>
    </div>
  );
}

function CreateEmissionsModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const headers = { "X-Entity-ID": String(entityId) };
  const currentYear = new Date().getFullYear();

  const [form, setForm] = useState({
    Title: "", Scope: "1", QuantityOrCost: "", Unit: "",
    Gas: "CO2", GasSubtype: "", Scope3Category: "",
    ProjectId: "", PhaseId: "", InventoryId: "",
    ReportingPeriodFrom: `${currentYear}-01-01`, ReportingPeriodTo: `${currentYear}-12-31`,
    SupplierName: "", ActivityDescription: "",
  });
  const [selectedEF, setSelectedEF] = useState<EmissionFactor | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: projectsData } = useQuery<{ results: Project[] }>({
    queryKey: ["projects-dropdown", entityId],
    queryFn: () => axiosInstance.get("/api/projects/", { headers }).then((r) => r.data),
  });
  const projects = projectsData?.results ?? [];

  const { data: inventoriesData } = useQuery<{ results: Inventory[] }>({
    queryKey: ["inventories-dropdown", entityId],
    queryFn: () =>
      axiosInstance.get("/api/ghg-inventories/", { headers }).then((r) => r.data),
    retry: false,
  });
  const inventories = (inventoriesData?.results ?? []).filter(
    (inventory) => inventory.VerificationStatus < 3,
  );

  const { data: phases = [] } = useQuery<ProjectPhase[]>({
    queryKey: ["project-phases-dropdown", entityId, form.ProjectId],
    queryFn: () =>
      axiosInstance
        .get(`/api/projects/${form.ProjectId}/phases/`, { headers })
        .then((r) => r.data),
    enabled: Boolean(form.ProjectId),
  });

  const mutation = useMutation({
    mutationFn: (data: CreateEmissionPayload) =>
      axiosInstance.post("/api/emissions/", data, { headers }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emissions", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string; errors?: Record<string, string[]> } } })
        ?.response?.data;
      if (detail?.errors) {
        const first = Object.values(detail.errors)[0]?.[0];
        setError(first ?? "Validation error.");
      } else {
        setError(detail?.detail ?? "Failed to create record.");
      }
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  function selectInventory(inventoryId: string) {
    const inventory = inventories.find(
      (candidate) => String(candidate.InventoryId) === inventoryId,
    );
    setForm((current) => ({
      ...current,
      InventoryId: inventoryId,
      ReportingPeriodFrom: inventory?.ReportingPeriodFrom ?? current.ReportingPeriodFrom,
      ReportingPeriodTo: inventory?.ReportingPeriodTo ?? current.ReportingPeriodTo,
    }));
  }

  function handleEFSelect(ef: EmissionFactor | null) {
    setSelectedEF(ef);
    if (ef) {
      setForm((f) => ({
        ...f,
        Gas:          ef.Gas,
        GasSubtype:   ef.GasSubtype ?? "",
        Unit:         ef.unit ?? f.Unit,
        Scope:        String(ef.Scope),
        Scope3Category: ef.Scope3Category ? String(ef.Scope3Category) : f.Scope3Category,
      }));
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!selectedEF) { setError("Please select an emission factor from the library."); return; }
    const reportingYear = new Date(`${form.ReportingPeriodTo}T00:00:00Z`).getUTCFullYear();
    mutation.mutate({
      Title:                form.Title,
      Scope:                Number(form.Scope),
      QuantityOrCost:       form.QuantityOrCost,
      Unit:                 form.Unit || selectedEF.unit || "unit",
      EmissionFactor:       selectedEF.FactorValue,
      EmissionFactorSource: `${selectedEF.set_name}${selectedEF.ApplicableYear ? ` ${selectedEF.ApplicableYear}` : ""}`,
      EmissionFactorId:     selectedEF.FactorId,
      Gas:                  form.Gas,
      GasSubtype:           form.GasSubtype || null,
      Scope3Category:       form.Scope === "3" && form.Scope3Category ? Number(form.Scope3Category) : null,
      ReportingPeriodFrom:  form.ReportingPeriodFrom,
      ReportingPeriodTo:    form.ReportingPeriodTo,
      ReportingYear:        reportingYear,
      ProjectId:            form.ProjectId ? Number(form.ProjectId) : null,
      PhaseId:              form.PhaseId ? Number(form.PhaseId) : null,
      InventoryId:          form.InventoryId ? Number(form.InventoryId) : null,
      SupplierName:         form.SupplierName || null,
      ActivityDescription:  form.ActivityDescription || null,
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-black/40 p-0">
      <div className="flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl">
        {/* Header */}
        <div className="flex shrink-0 items-start justify-between border-b border-surface-200 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-surface-900">Add GHG Emission Details</h2>
            <p className="mt-0.5 text-xs text-surface-400">Enter emissions or reduction data from project activities.</p>
          </div>
          <button onClick={onClose} className="btn-ghost btn-sm mt-0.5"><X className="h-4 w-4" /></button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {error && (
            <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
          )}

          <form id="emission-form" onSubmit={handleSubmit} className="space-y-6">
            {/* Activity & Timing */}
            <div>
              <SectionHeading>Activity &amp; Timing</SectionHeading>
              <div className="space-y-3">
                <div>
                  <label className="label mb-1">Title <span className="text-red-400">*</span></label>
                  <input className="input" required placeholder="e.g. Natural gas — boiler room"
                    value={form.Title} onChange={(e) => set("Title", e.target.value)} />
                </div>
                <div>
                  <label className="label mb-1">
                    Formal inventory <span className="font-normal text-surface-400">optional</span>
                  </label>
                  <select
                    className="input"
                    value={form.InventoryId}
                    onChange={(e) => selectInventory(e.target.value)}
                  >
                    <option value="">— unassigned working record —</option>
                    {inventories.map((inventory) => (
                      <option key={inventory.InventoryId} value={inventory.InventoryId}>
                        {inventory.ReportingYear} · {inventory.ReportingPeriodFrom} to {inventory.ReportingPeriodTo}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-surface-400">
                    Assigned records contribute only to this inventory. Selecting one aligns the reporting period and GWP dataset.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Project <span className="font-normal text-surface-400">optional</span></label>
                    <select
                      className="input"
                      value={form.ProjectId}
                      onChange={(e) =>
                        setForm((current) => ({
                          ...current,
                          ProjectId: e.target.value,
                          PhaseId: "",
                        }))
                      }
                    >
                      <option value="">— no project —</option>
                      {projects.map((p) => (
                        <option key={p.ProjectId} value={p.ProjectId}>{p.ProjectName}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label mb-1">Phase <span className="font-normal text-surface-400">optional</span></label>
                    <select
                      className="input"
                      value={form.PhaseId}
                      disabled={!form.ProjectId}
                      onChange={(e) => set("PhaseId", e.target.value)}
                    >
                      <option value="">— no phase —</option>
                      {phases.map((phase) => (
                        <option key={phase.PhaseId} value={phase.PhaseId}>
                          {phase.PhaseNumber ? `${phase.PhaseNumber}. ` : ""}{phase.PhaseName}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Period from <span className="text-red-400">*</span></label>
                    <input className="input" required type="date" value={form.ReportingPeriodFrom} onChange={(e) => set("ReportingPeriodFrom", e.target.value)} />
                  </div>
                  <div>
                    <label className="label mb-1">Period to <span className="text-red-400">*</span></label>
                    <input className="input" required type="date" value={form.ReportingPeriodTo} onChange={(e) => set("ReportingPeriodTo", e.target.value)} />
                  </div>
                </div>
                <p className="text-xs text-surface-400">
                  Reporting year is derived from the period end date.
                </p>
              </div>
            </div>

            {/* Scope */}
            <div>
              <SectionHeading>GHG Scope</SectionHeading>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label mb-1">Scope <span className="text-red-400">*</span></label>
                  <select className="input" value={form.Scope} onChange={(e) => set("Scope", e.target.value)}>
                    <option value="1">Scope 1 — Direct</option>
                    <option value="2">Scope 2 — Electricity</option>
                    <option value="3">Scope 3 — Value chain</option>
                  </select>
                </div>
                {form.Scope === "3" && (
                  <div>
                    <label className="label mb-1">Category (1–15)</label>
                    <input className="input" type="number" min={1} max={15}
                      value={form.Scope3Category} onChange={(e) => set("Scope3Category", e.target.value)} />
                  </div>
                )}
              </div>
            </div>

            {/* Supplier */}
            <div>
              <SectionHeading>Supplier <span className="font-normal normal-case text-surface-400">— optional</span></SectionHeading>
              <input className="input" placeholder="e.g. National Grid"
                value={form.SupplierName} onChange={(e) => set("SupplierName", e.target.value)} />
            </div>

            {/* Emission Factor */}
            <div>
              <SectionHeading>Emission Factor &amp; Quantity</SectionHeading>
              <div className="space-y-3">
                <div>
                  <label className="label mb-1">
                    Emission factor <span className="text-red-400">*</span>
                    <span className="ml-1 font-normal text-surface-400 text-xs">(kg CO₂e / unit)</span>
                  </label>
                  <EFPicker
                    scope={form.Scope ? Number(form.Scope) : undefined}
                    value={selectedEF}
                    onChange={handleEFSelect}
                  />
                  {selectedEF && (
                    <p className="mt-1 text-xs text-surface-400">
                      Gas: <span className="font-medium text-surface-600">{selectedEF.Gas}</span>
                      {selectedEF.GasSubtype && ` (${selectedEF.GasSubtype})`}
                      {" · "}Factor: <span className="font-mono font-medium text-surface-600">{selectedEF.FactorValue}</span>
                      {" · "}Source: <span className="text-surface-600">{selectedEF.set_name}</span>
                    </p>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Quantity <span className="text-red-400">*</span></label>
                    <input className="input" type="number" step="any" required
                      value={form.QuantityOrCost} onChange={(e) => set("QuantityOrCost", e.target.value)} />
                  </div>
                  <div>
                    <label className="label mb-1">Unit <span className="text-red-400">*</span></label>
                    <input className="input" required placeholder="litres, kWh, km…"
                      value={form.Unit} onChange={(e) => set("Unit", e.target.value)} />
                  </div>
                </div>

                <p className="text-xs text-surface-400">
                  The server applies the recorded factor, unit conversion, and GWP dataset on save.
                </p>
              </div>
            </div>

            {/* Notes */}
            <div>
              <SectionHeading>Notes</SectionHeading>
              <textarea className="input resize-y min-h-[72px]" rows={3} placeholder="Additional context, data source, assumptions…"
                value={form.ActivityDescription} onChange={(e) => set("ActivityDescription", e.target.value)} />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-surface-200 bg-surface-50 px-6 py-4">
          <div className="flex items-center justify-end">
            <div className="flex gap-2">
              <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
              <button form="emission-form" type="submit" disabled={mutation.isPending} className="btn-primary">
                {mutation.isPending ? "Saving…" : "Save record"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function EmissionsPage() {
  const { activeEntityId } = useAuthStore();
  const [showCreate, setShowCreate] = useState(false);
  const [scopeFilter, setScopeFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["emissions", activeEntityId, scopeFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (scopeFilter) params.set("scope", scopeFilter);
      return axiosInstance
        .get<{ results: EmissionsRecord[]; count: number }>(
          `/api/emissions/?${params}`,
          { headers: activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {} },
        )
        .then((r) => r.data);
    },
    enabled: !!activeEntityId,
  });

  const records = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Emissions</h1>
          <p className="page-subtitle">{data?.count ?? 0} records</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + New record
        </button>
      </div>

      {/* Scope filters */}
      <div className="flex gap-2">
        {["", "1", "2", "3"].map((s) => (
          <button
            key={s}
            onClick={() => setScopeFilter(s)}
            className={`btn-sm ${scopeFilter === s ? "btn-primary" : "btn-secondary"}`}
          >
            {s === "" ? "All" : `Scope ${s}`}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : records.length === 0 ? (
          <EmptyState
            message="No emissions records yet."
            action={{ label: "+ New record", onClick: () => setShowCreate(true) }}
          />
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Title</th>
                <th>Scope</th>
                <th>Gas</th>
                <th className="text-right">tCO₂e</th>
                <th>Year</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => {
                const verif = VERIF_LABELS[r.VerificationStatus] ?? VERIF_LABELS[1];
                return (
                  <tr key={r.EmissionsId}>
                    <td className="max-w-[240px] truncate font-medium">
                      <Link href={`/emissions/${r.EmissionsId}`} className="text-brand-700 hover:underline">{r.Title}</Link>
                    </td>
                    <td><span className="badge badge-slate">{SCOPE_LABELS[r.Scope]}</span></td>
                    <td className="text-surface-500">{r.Gas}</td>
                    <td className="text-right tabular-nums">
                      {r.EmissionsAmountTonnes
                        ? parseFloat(r.EmissionsAmountTonnes).toFixed(3)
                        : "—"}
                    </td>
                    <td className="text-surface-500">{r.ReportingYear ?? "—"}</td>
                    <td><span className={`badge ${verif.cls}`}>{verif.label}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && activeEntityId && (
        <CreateEmissionsModal
          entityId={activeEntityId}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}

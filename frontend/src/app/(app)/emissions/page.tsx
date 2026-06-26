"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Upload } from "lucide-react";
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

const SCOPE_LABELS: Record<number, string> = { 1: "Scope 1", 2: "Scope 2", 3: "Scope 3" };
const VERIF_LABELS: Record<number, { label: string; cls: string }> = {
  1: { label: "Unverified", cls: "badge-slate" },
  2: { label: "Pending",    cls: "badge-yellow" },
  3: { label: "Verified",   cls: "badge-green" },
  4: { label: "3rd Party",  cls: "badge-green" },
};

const SUPPLIER_CATEGORIES = [
  "Energy", "Transport", "Waste", "Water", "Materials",
  "Purchased Goods", "Capital Goods", "Business Travel", "Other",
];

const GWP_DATASET_ID = 1;

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

  const [form, setForm] = useState({
    Title: "", Scope: "1", QuantityOrCost: "", Unit: "",
    Gas: "CO2", GasSubtype: "", Scope3Category: "", ReportingYear: String(new Date().getFullYear()),
    ProjectId: "", DateFrom: "", DateTo: "", Supplier: "", SupplierCategory: "", Remarks: "",
  });
  const [selectedEF, setSelectedEF] = useState<EmissionFactor | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const { data: projectsData } = useQuery<{ results: Project[] }>({
    queryKey: ["projects-dropdown", entityId],
    queryFn: () => axiosInstance.get("/api/projects/", { headers }).then((r) => r.data),
  });
  const projects = projectsData?.results ?? [];

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
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

  function set(k: string, v: string) { setForm((f) => ({ ...f, [k]: v })); }

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
      ReportingYear:        form.ReportingYear ? Number(form.ReportingYear) : null,
      GwpDatasetId:         GWP_DATASET_ID,
      ProjectId:            form.ProjectId ? Number(form.ProjectId) : null,
      DateFrom:             form.DateFrom || null,
      DateTo:               form.DateTo   || null,
      Supplier:             form.Supplier || null,
      SupplierCategory:     form.SupplierCategory || null,
      Remarks:              form.Remarks || null,
    });
  }

  const estTonnes = selectedEF && form.QuantityOrCost
    ? (parseFloat(form.QuantityOrCost) * selectedEF.FactorValue / 1000).toFixed(4)
    : null;

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
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Project <span className="font-normal text-surface-400">optional</span></label>
                    <select className="input" value={form.ProjectId} onChange={(e) => set("ProjectId", e.target.value)}>
                      <option value="">— no project —</option>
                      {projects.map((p) => (
                        <option key={p.ProjectId} value={p.ProjectId}>{p.ProjectName}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label mb-1">Reporting year</label>
                    <input className="input" type="number" min={2000} max={2100}
                      value={form.ReportingYear} onChange={(e) => set("ReportingYear", e.target.value)} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="label mb-1">Date from <span className="font-normal text-surface-400">optional</span></label>
                    <input className="input" type="date" value={form.DateFrom} onChange={(e) => set("DateFrom", e.target.value)} />
                  </div>
                  <div>
                    <label className="label mb-1">Date to <span className="font-normal text-surface-400">optional</span></label>
                    <input className="input" type="date" value={form.DateTo} onChange={(e) => set("DateTo", e.target.value)} />
                  </div>
                </div>
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
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label mb-1">Supplier name</label>
                  <input className="input" placeholder="e.g. National Grid"
                    value={form.Supplier} onChange={(e) => set("Supplier", e.target.value)} />
                </div>
                <div>
                  <label className="label mb-1">Supplier category</label>
                  <select className="input" value={form.SupplierCategory} onChange={(e) => set("SupplierCategory", e.target.value)}>
                    <option value="">— select —</option>
                    {SUPPLIER_CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
              </div>
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

                {/* Live estimate */}
                {estTonnes && (
                  <div className="flex items-center gap-2 rounded-md bg-brand-50 border border-brand-100 px-3 py-2">
                    <span className="text-xs text-brand-700">Estimated emissions:</span>
                    <span className="text-sm font-semibold font-mono text-brand-800">{estTonnes} tCO₂e</span>
                    <span className="text-xs text-brand-500 ml-1">(server will recalculate on save)</span>
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            <div>
              <SectionHeading>Notes</SectionHeading>
              <textarea className="input resize-y min-h-[72px]" rows={3} placeholder="Additional context, data source, assumptions…"
                value={form.Remarks} onChange={(e) => set("Remarks", e.target.value)} />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-surface-200 bg-surface-50 px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Bulk upload stub */}
            <label className="flex cursor-pointer items-center gap-2 text-sm text-surface-500 hover:text-surface-700">
              <Upload className="h-4 w-4" />
              <span>Upload Excel</span>
              <input type="file" accept=".xlsx,.xls,.csv" className="sr-only"
                onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)} />
            </label>
            {uploadFile && (
              <span className="text-xs text-brand-600 truncate max-w-[140px]">{uploadFile.name}</span>
            )}
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
            action={{ label: "+ New record", href: "#" }}
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
                    <td className="max-w-[240px] truncate font-medium">{r.Title}</td>
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

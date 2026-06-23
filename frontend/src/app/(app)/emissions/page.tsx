"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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

const SCOPE_LABELS: Record<number, string> = { 1: "Scope 1", 2: "Scope 2", 3: "Scope 3" };
const VERIF_LABELS: Record<number, { label: string; cls: string }> = {
  1: { label: "Unverified", cls: "badge-slate" },
  2: { label: "Pending",    cls: "badge-yellow" },
  3: { label: "Verified",   cls: "badge-green" },
  4: { label: "3rd Party",  cls: "badge-green" },
  5: { label: "CDP",        cls: "badge-blue" },
};

const GWP_DATASET_ID = 1; // IPCC AR6 — seeded on first deploy

function CreateEmissionsModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    Title: "", Scope: "1", QuantityOrCost: "", Unit: "",
    Gas: "CO2", GasSubtype: "", Scope3Category: "",
    ReportingYear: String(new Date().getFullYear()),
  });
  const [selectedEF, setSelectedEF] = useState<EmissionFactor | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      axiosInstance.post("/api/emissions/", data, {
        headers: { "X-Entity-ID": String(entityId) },
      }).then((r) => r.data),
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
        Gas:      ef.Gas,
        GasSubtype: ef.GasSubtype ?? "",
        Unit:     ef.unit ?? f.Unit,
        Scope:    String(ef.Scope),
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
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold text-surface-900">New emissions record</h2>
          <button onClick={onClose} className="btn-ghost btn-sm">✕</button>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label mb-1">Title</label>
            <input className="input" required value={form.Title}
              onChange={(e) => set("Title", e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Scope</label>
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
            <div>
              <label className="label mb-1">Reporting year</label>
              <input className="input" type="number" min={2000} max={2100}
                value={form.ReportingYear} onChange={(e) => set("ReportingYear", e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Quantity</label>
              <input className="input" type="number" step="any" required
                value={form.QuantityOrCost} onChange={(e) => set("QuantityOrCost", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Unit</label>
              <input className="input" required
                value={form.Unit} onChange={(e) => set("Unit", e.target.value)}
                placeholder="litres, kWh, km…" />
            </div>
          </div>

          <div>
            <label className="label mb-1">
              Emission factor
              <span className="ml-1 text-surface-400 font-normal text-xs">(kg CO₂e/unit)</span>
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
                {" · "}Value: <span className="font-mono font-medium text-surface-600">{selectedEF.FactorValue}</span>
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2">
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

      {/* Filters */}
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

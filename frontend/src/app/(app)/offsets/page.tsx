"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, ExternalLink, RefreshCw } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { EmptyState } from "@/components/EmptyState";

interface Offset {
  OffsetId:                    number;
  EmissionsId:                 number;
  Title:                       string;
  OffsetType:                  string;
  Provider:                    string;
  CertificateNumber:           string | null;
  OffsetAmountTonnes:          string;
  ValidFrom:                   string | null;
  ValidTo:                     string | null;
  CreditSerialNumber:          string | null;
  RegistryValidationStatus:    string | null;
  RegistryProjectName:         string | null;
  RegistryProjectType:         string | null;
  RegistryVintageYear:         number | null;
  RegistryRetirementBeneficiary: string | null;
  Remarks:                     string | null;
}

interface EmissionsRecord { EmissionsId: number; Title: string; ReportingYear: number | null; }

const OFFSET_TYPES = [
  "Voluntary Carbon Unit (VCU)", "Gold Standard (GS)", "Verified Emission Reduction (VER)",
  "Renewable Energy Certificate (REC)", "REDD+", "Biochar", "Blue Carbon", "Other",
];

const REGISTRY_STATUS: Record<string, { label: string; cls: string }> = {
  unverified: { label: "Unverified",  cls: "badge-slate"  },
  pending:    { label: "Pending",     cls: "badge-yellow" },
  valid:      { label: "Valid",       cls: "badge-green"  },
  invalid:    { label: "Invalid",     cls: "badge-red"    },
};

function CreateOffsetModal({ onClose, entityId, emissionsRecords }: {
  onClose: () => void;
  entityId: number;
  emissionsRecords: EmissionsRecord[];
}) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    EmissionsId: "",
    Title: "", OffsetType: "Voluntary Carbon Unit (VCU)", Provider: "",
    CertificateNumber: "", OffsetAmountTonnes: "",
    ValidFrom: "", ValidTo: "",
    CreditSerialNumber: "", RegistryVintageYear: "",
    Remarks: "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () => axiosInstance.post("/api/emissions-offsets/", {
      EmissionsId:          form.EmissionsId ? Number(form.EmissionsId) : null,
      Title:                form.Title,
      OffsetType:           form.OffsetType,
      Provider:             form.Provider,
      CertificateNumber:    form.CertificateNumber    || null,
      OffsetAmountTonnes:   Number(form.OffsetAmountTonnes),
      ValidFrom:            form.ValidFrom             || null,
      ValidTo:              form.ValidTo               || null,
      CreditSerialNumber:   form.CreditSerialNumber    || null,
      RegistryVintageYear:  form.RegistryVintageYear ? Number(form.RegistryVintageYear) : null,
      Remarks:              form.Remarks               || null,
    }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offsets", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to save offset.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold">New carbon offset</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div>
            <label className="label mb-1">Link to emissions record <span className="font-normal text-surface-400">optional</span></label>
            <select className="input" value={form.EmissionsId} onChange={(e) => set("EmissionsId", e.target.value)}>
              <option value="">— none —</option>
              {emissionsRecords.map((r) => (
                <option key={r.EmissionsId} value={r.EmissionsId}>
                  {r.Title}{r.ReportingYear ? ` (${r.ReportingYear})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label mb-1">Title</label>
            <input className="input" required placeholder="e.g. REDD+ Forest Protection — Amazon Basin"
              value={form.Title} onChange={(e) => set("Title", e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Offset type</label>
              <select className="input" value={form.OffsetType} onChange={(e) => set("OffsetType", e.target.value)}>
                {OFFSET_TYPES.map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label mb-1">Provider / registry</label>
              <input className="input" required placeholder="Verra, Gold Standard…"
                value={form.Provider} onChange={(e) => set("Provider", e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Amount (tCO₂e)</label>
              <input className="input" type="number" step="any" min="0" required
                value={form.OffsetAmountTonnes} onChange={(e) => set("OffsetAmountTonnes", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Vintage year</label>
              <input className="input" type="number" min={2000} max={2100}
                placeholder="e.g. 2023"
                value={form.RegistryVintageYear} onChange={(e) => set("RegistryVintageYear", e.target.value)} />
            </div>
          </div>

          <div>
            <label className="label mb-1">
              Credit serial number{" "}
              <span className="font-normal text-surface-400">— used for Verra/GS registry validation</span>
            </label>
            <input className="input font-mono text-xs" placeholder="VCS-XXXX-XXXXX"
              value={form.CreditSerialNumber} onChange={(e) => set("CreditSerialNumber", e.target.value)} />
            <p className="mt-1 text-xs text-surface-400">
              The nightly sync validates this against the Verra and Gold Standard registries automatically.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Certificate number <span className="font-normal text-surface-400">optional</span></label>
              <input className="input" value={form.CertificateNumber}
                onChange={(e) => set("CertificateNumber", e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Valid from</label>
              <input className="input" type="date" value={form.ValidFrom}
                onChange={(e) => set("ValidFrom", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Valid to</label>
              <input className="input" type="date" value={form.ValidTo}
                onChange={(e) => set("ValidTo", e.target.value)} />
            </div>
          </div>

          <div>
            <label className="label mb-1">Remarks <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[60px]" rows={2}
              value={form.Remarks} onChange={(e) => set("Remarks", e.target.value)} />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Save offset"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function OffsetsPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: Offset[] }>({
    queryKey: ["offsets", activeEntityId],
    queryFn: () => axiosInstance.get("/api/emissions-offsets/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const { data: emData } = useQuery<{ results: EmissionsRecord[] }>({
    queryKey: ["emissions-list", activeEntityId],
    queryFn: () => axiosInstance.get("/api/emissions/?page_size=200", { headers })
      .then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const softDelete = useMutation({
    mutationFn: (id: number) =>
      axiosInstance.delete(`/api/emissions-offsets/${id}/`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["offsets", activeEntityId] }),
  });

  const offsets = (data?.results ?? []).filter((o) => (o as unknown as { Status: number }).Status !== 4);
  const emRecords = emData?.results ?? [];

  const totalTonnes = offsets.reduce((a, o) => a + parseFloat(o.OffsetAmountTonnes || "0"), 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Carbon Offsets</h1>
          <p className="page-subtitle">
            {offsets.length} offset{offsets.length !== 1 ? "s" : ""} ·{" "}
            <span className="font-medium text-brand-700">{totalTonnes.toFixed(2)} tCO₂e</span> total
          </p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> New offset
        </button>
      </div>

      {/* Registry sync note */}
      <div className="rounded-lg border border-surface-200 bg-surface-50 px-4 py-3 flex items-start gap-3 text-sm text-surface-500">
        <RefreshCw className="h-4 w-4 mt-0.5 text-surface-400 shrink-0" />
        <span>
          Offsets with a credit serial number are validated against the{" "}
          <a href="https://registry.verra.org" target="_blank" rel="noopener noreferrer"
            className="text-brand-600 hover:underline inline-flex items-center gap-0.5">
            Verra VCS registry <ExternalLink className="h-3 w-3" />
          </a>
          {" "}and Gold Standard automatically — the nightly Celery task updates RegistryValidationStatus.
        </span>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : offsets.length === 0 ? (
          <EmptyState
            message="No carbon offsets yet."
            action={{ label: "+ New offset", href: "#" }}
          />
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Provider</th>
                <th className="text-right">Amount (tCO₂e)</th>
                <th>Vintage</th>
                <th>Serial number</th>
                <th>Registry status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {offsets.map((o) => {
                const rs = REGISTRY_STATUS[o.RegistryValidationStatus ?? "unverified"] ?? REGISTRY_STATUS.unverified;
                return (
                  <tr key={o.OffsetId}>
                    <td>
                      <p className="font-medium leading-snug">
                        <Link href={`/offsets/${o.OffsetId}`} className="text-brand-700 hover:underline">{o.Title}</Link>
                      </p>
                      {o.RegistryProjectName && (
                        <p className="text-xs text-surface-400 mt-0.5 truncate max-w-[200px]">
                          {o.RegistryProjectName}
                        </p>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-slate text-xs">{o.OffsetType.split(" (")[0]}</span>
                    </td>
                    <td className="text-surface-600 text-sm">{o.Provider}</td>
                    <td className="text-right tabular-nums font-medium text-brand-700">
                      {parseFloat(o.OffsetAmountTonnes).toFixed(2)}
                    </td>
                    <td className="text-surface-500 text-sm">{o.RegistryVintageYear ?? "—"}</td>
                    <td>
                      {o.CreditSerialNumber
                        ? <code className="text-xs bg-surface-100 px-1.5 py-0.5 rounded font-mono">
                            {o.CreditSerialNumber}
                          </code>
                        : <span className="text-surface-400 text-xs">—</span>}
                    </td>
                    <td>
                      <span className={`badge ${rs.cls} text-xs`}>{rs.label}</span>
                    </td>
                    <td className="text-right">
                      <button
                        className="btn-ghost btn-sm text-xs text-red-500 hover:text-red-700"
                        onClick={() => { if (confirm(`Delete "${o.Title}"?`)) softDelete.mutate(o.OffsetId); }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && activeEntityId && (
        <CreateOffsetModal
          entityId={activeEntityId}
          emissionsRecords={emRecords}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}

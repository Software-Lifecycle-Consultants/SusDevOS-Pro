"use client";

import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, RefreshCw } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

const ENTITY_TYPES = [
  { value: 1, label: "Limited Company" },
  { value: 2, label: "PLC" },
  { value: 3, label: "LLP" },
  { value: 4, label: "Partnership" },
  { value: 5, label: "Sole Trader" },
  { value: 6, label: "Charity" },
  { value: 7, label: "Public Body" },
  { value: 8, label: "Other" },
];

const CONSOLIDATION = [
  { value: 1, label: "Equity Share" },
  { value: 2, label: "Financial Control" },
  { value: 3, label: "Operational Control" },
];

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

interface Entity {
  EntityId:             number;
  EntityName:           string;
  EntityType:           number | null;
  RegistrationNumber:   string | null;
  VATNumber:            string | null;
  AddressLine1:         string | null;
  AddressLine2:         string | null;
  City:                 string | null;
  PostCode:             string | null;
  Country:              string | null;
  BaseCurrency:         string;
  FiscalYearEndMonth:   number;
  ConsolidationApproach: number | null;
  CompaniesHouseNumber: string | null;
}

export default function EntitySettingsPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [chLoading, setChLoading] = useState(false);
  const [chError, setChError] = useState<string | null>(null);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data: entity, isLoading } = useQuery<Entity>({
    queryKey: ["entity", activeEntityId],
    queryFn: () =>
      axiosInstance.get(`/api/entities/${activeEntityId}/`, { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const [form, setForm] = useState<Partial<Entity>>({});

  useEffect(() => {
    if (entity) setForm(entity);
  }, [entity]);

  const mutation = useMutation({
    mutationFn: (data: Partial<Entity>) =>
      axiosInstance.patch(`/api/entities/${activeEntityId}/`, data, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["entity", activeEntityId] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    },
  });

  function set<K extends keyof Entity>(key: K, value: Entity[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function populateFromCH() {
    const chNumber = form.CompaniesHouseNumber?.trim() || form.RegistrationNumber?.trim();
    if (!chNumber) { setChError("Enter a Companies House number first."); return; }
    setChLoading(true); setChError(null);
    try {
      const { data } = await axiosInstance.get(
        `/api/entities/${activeEntityId}/companies-house/?number=${encodeURIComponent(chNumber)}`,
        { headers },
      );
      setForm((f) => ({
        ...f,
        EntityName:         data.EntityName         ?? f.EntityName,
        AddressLine1:       data.AddressLine1       ?? f.AddressLine1,
        AddressLine2:       data.AddressLine2       ?? f.AddressLine2,
        City:               data.City               ?? f.City,
        PostCode:           data.PostCode           ?? f.PostCode,
        Country:            data.Country            ?? f.Country,
        RegistrationNumber: data.RegistrationNumber ?? f.RegistrationNumber,
      }));
    } catch {
      setChError("Could not fetch from Companies House. Check the number and try again.");
    } finally {
      setChLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(form);
  }

  if (!activeEntityId) return (
    <div className="card p-6 text-sm text-surface-500">No organisation selected.</div>
  );

  if (isLoading) return (
    <div className="card p-6 flex items-center gap-2 text-sm text-surface-500">
      <Loader2 className="h-4 w-4 animate-spin" /> Loading…
    </div>
  );

  const inputCls = "input";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic details */}
      <div className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-surface-800 mb-2">Organisation details</h2>

        <div>
          <label className="label mb-1">Legal name</label>
          <input className={inputCls} value={form.EntityName ?? ""} required
            onChange={(e) => set("EntityName", e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label mb-1">Entity type</label>
            <select className={inputCls} value={form.EntityType ?? ""}
              onChange={(e) => set("EntityType", e.target.value ? Number(e.target.value) : null)}>
              <option value="">— select —</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label mb-1">Base currency</label>
            <input className={inputCls} maxLength={3} placeholder="GBP"
              value={form.BaseCurrency ?? "GBP"}
              onChange={(e) => set("BaseCurrency", e.target.value.toUpperCase())} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label mb-1">Fiscal year end month</label>
            <select className={inputCls} value={form.FiscalYearEndMonth ?? 3}
              onChange={(e) => set("FiscalYearEndMonth", Number(e.target.value))}>
              {MONTHS.map((m, i) => (
                <option key={i + 1} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label mb-1">GHG consolidation approach</label>
            <select className={inputCls} value={form.ConsolidationApproach ?? ""}
              onChange={(e) => set("ConsolidationApproach", e.target.value ? Number(e.target.value) : null)}>
              <option value="">— select —</option>
              {CONSOLIDATION.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Registration */}
      <div className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-surface-800 mb-2">Registration numbers</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label mb-1">Companies House number</label>
            <div className="flex gap-2">
              <input className={`${inputCls} flex-1`} placeholder="12345678"
                value={form.CompaniesHouseNumber ?? form.RegistrationNumber ?? ""}
                onChange={(e) => set("CompaniesHouseNumber", e.target.value)} />
              <button type="button" onClick={populateFromCH} disabled={chLoading}
                className="btn-secondary shrink-0 flex items-center gap-1.5 text-xs">
                {chLoading
                  ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  : <RefreshCw className="h-3.5 w-3.5" />}
                Auto-fill
              </button>
            </div>
            {chError && <p className="mt-1 text-xs text-red-600">{chError}</p>}
            <p className="mt-1 text-xs text-surface-400">Auto-fills address from Companies House API</p>
          </div>
          <div>
            <label className="label mb-1">VAT number</label>
            <input className={inputCls} placeholder="GB 123 4567 89"
              value={form.VATNumber ?? ""}
              onChange={(e) => set("VATNumber", e.target.value)} />
          </div>
        </div>
      </div>

      {/* Address */}
      <div className="card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-surface-800 mb-2">Registered address</h2>

        <div>
          <label className="label mb-1">Address line 1</label>
          <input className={inputCls} value={form.AddressLine1 ?? ""}
            onChange={(e) => set("AddressLine1", e.target.value)} />
        </div>
        <div>
          <label className="label mb-1">Address line 2</label>
          <input className={inputCls} value={form.AddressLine2 ?? ""}
            onChange={(e) => set("AddressLine2", e.target.value)} />
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label mb-1">City</label>
            <input className={inputCls} value={form.City ?? ""}
              onChange={(e) => set("City", e.target.value)} />
          </div>
          <div>
            <label className="label mb-1">Post code</label>
            <input className={inputCls} value={form.PostCode ?? ""}
              onChange={(e) => set("PostCode", e.target.value)} />
          </div>
          <div>
            <label className="label mb-1">Country</label>
            <input className={inputCls} value={form.Country ?? ""}
              onChange={(e) => set("Country", e.target.value)} />
          </div>
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-3">
        <button type="submit" disabled={mutation.isPending} className="btn-primary">
          {mutation.isPending ? "Saving…" : "Save changes"}
        </button>
        {saved && <p className="text-sm text-brand-600 font-medium">Saved ✓</p>}
        {mutation.isError && (
          <p className="text-sm text-red-600">Failed to save. Please try again.</p>
        )}
      </div>
    </form>
  );
}

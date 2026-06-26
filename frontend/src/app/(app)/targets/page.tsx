"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ChevronDown, ChevronRight, X, TrendingDown } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface Target {
  TargetId:                number;
  TargetName:              string;
  TargetType:              string;
  BaselineYear:            number;
  TargetYear:              number;
  BaselineEmissionsTonnes: string | null;
  ReductionPercent:        string | null;
  Scope:                   number | null;
  ValidationStatus:        number;
  Notes:                   string | null;
}

interface Milestone {
  MilestoneId:             number;
  MilestoneYear:           number;
  TargetEmissionsTonnes:   string | null;
  ActualEmissionsTonnes:   string | null;
  IsAchieved:              boolean;
  Notes:                   string | null;
}

const TARGET_TYPE_LABELS: Record<string, string> = {
  near_term:  "Near-term",
  long_term:  "Long-term",
  net_zero:   "Net-zero",
  intensity:  "Intensity",
};

const VALIDATION_LABELS: Record<number, { label: string; badge: string }> = {
  1: { label: "Draft",    badge: "badge-slate" },
  2: { label: "Active",   badge: "badge-green" },
  3: { label: "Achieved", badge: "badge-blue"  },
  4: { label: "Missed",   badge: "badge-red"   },
};

function fmt(v: string | null, dp = 2) {
  return v ? parseFloat(v).toFixed(dp) : "—";
}

function MilestoneProgress({ target, actual, baseline }: {
  target: string | null; actual: string | null; baseline: string | null;
}) {
  if (!target) return <span className="text-surface-400 text-xs">—</span>;
  const t = parseFloat(target);
  const a = actual ? parseFloat(actual) : null;
  const b = baseline ? parseFloat(baseline) : null;
  const onTrack = a !== null && a <= t;

  return (
    <div className="space-y-1 min-w-[180px]">
      <div className="flex justify-between text-xs text-surface-500">
        <span>Target: {fmt(target)} t</span>
        {a !== null && <span className={onTrack ? "text-brand-600" : "text-red-600"}>
          Actual: {fmt(actual)} t
        </span>}
      </div>
      {b && (
        <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
          <div className="h-full bg-brand-200 rounded-full" style={{ width: `${Math.min(100, (t / b) * 100)}%` }} />
          {a !== null && (
            <div
              className={`h-full -mt-1.5 rounded-full ${onTrack ? "bg-brand-600" : "bg-red-500"}`}
              style={{ width: `${Math.min(100, (a / b) * 100)}%` }}
            />
          )}
        </div>
      )}
    </div>
  );
}

function MilestonesRow({ target, headers }: { target: Target; headers: Record<string, string> }) {
  const { data, isLoading } = useQuery<Milestone[]>({
    queryKey: ["milestones", target.TargetId],
    queryFn: () =>
      axiosInstance.get(`/api/targets/${target.TargetId}/milestones/`, { headers })
        .then((r) => r.data),
  });

  if (isLoading) return (
    <tr><td colSpan={6} className="px-4 py-3 text-xs text-surface-400">Loading milestones…</td></tr>
  );

  const milestones = Array.isArray(data) ? data : [];
  if (milestones.length === 0) return (
    <tr><td colSpan={6} className="px-4 py-3 text-xs text-surface-400 italic">
      No milestones. The nightly task links verified inventories to milestones automatically.
    </td></tr>
  );

  return (
    <>
      <tr className="bg-brand-50">
        <td colSpan={6} className="px-8 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-brand-600">
            Milestones — {target.TargetName}
          </p>
        </td>
      </tr>
      {milestones.map((m) => (
        <tr key={m.MilestoneId} className="bg-brand-50/50 border-t border-brand-100">
          <td className="pl-10 pr-4 py-2.5 text-sm text-surface-700">{m.MilestoneYear}</td>
          <td colSpan={2} className="px-4 py-2.5">
            <MilestoneProgress
              target={m.TargetEmissionsTonnes}
              actual={m.ActualEmissionsTonnes}
              baseline={target.BaselineEmissionsTonnes}
            />
          </td>
          <td className="px-4 py-2.5 text-sm tabular-nums text-surface-600">{fmt(m.TargetEmissionsTonnes)}</td>
          <td className="px-4 py-2.5 text-sm tabular-nums text-surface-600">{fmt(m.ActualEmissionsTonnes)}</td>
          <td className="px-4 py-2.5">
            {m.IsAchieved
              ? <span className="badge badge-green text-xs">Achieved</span>
              : m.ActualEmissionsTonnes
                ? <span className="badge badge-red text-xs">Missed</span>
                : <span className="text-surface-400 text-xs">Pending</span>}
          </td>
          <td className="px-4 py-2.5 text-xs text-surface-400 truncate max-w-[140px]">{m.Notes ?? "—"}</td>
        </tr>
      ))}
    </>
  );
}

function CreateTargetModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    TargetName:    "",
    TargetType:    "near_term",
    BaselineYear:  "2019",
    TargetYear:    "2030",
    ReductionPercent: "",
    BaselineEmissionsTonnes: "",
    Scope:         "",
    Notes:         "",
  });
  const [error, setError] = useState<string | null>(null);
  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () =>
      axiosInstance.post("/api/targets/", {
        TargetName:              form.TargetName,
        TargetType:              form.TargetType,
        BaselineYear:            Number(form.BaselineYear),
        TargetYear:              Number(form.TargetYear),
        ReductionPercent:        form.ReductionPercent ? Number(form.ReductionPercent) : null,
        BaselineEmissionsTonnes: form.BaselineEmissionsTonnes ? Number(form.BaselineEmissionsTonnes) : null,
        Scope:                   form.Scope ? Number(form.Scope) : null,
        Notes:                   form.Notes || null,
      }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["targets", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const first = d ? Object.values(d)[0] : null;
      setError(Array.isArray(first) ? first[0] as string : "Failed to create target.");
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-surface-900">New reduction target</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>
        {error && <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div>
            <label className="label mb-1">Target name</label>
            <input className="input" required placeholder="e.g. 50% Scope 1+2 reduction by 2030"
              value={form.TargetName} onChange={(e) => set("TargetName", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Target type</label>
              <select className="input" value={form.TargetType} onChange={(e) => set("TargetType", e.target.value)}>
                {Object.entries(TARGET_TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label mb-1">Scope <span className="font-normal text-surface-400">(optional)</span></label>
              <select className="input" value={form.Scope} onChange={(e) => set("Scope", e.target.value)}>
                <option value="">All scopes</option>
                <option value="1">Scope 1</option>
                <option value="2">Scope 2</option>
                <option value="3">Scope 3</option>
                <option value="12">Scope 1+2</option>
                <option value="123">Scope 1+2+3</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="label mb-1">Baseline year</label>
              <input className="input" type="number" min={2000} max={2100} required
                value={form.BaselineYear} onChange={(e) => set("BaselineYear", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Target year</label>
              <input className="input" type="number" min={2000} max={2100} required
                value={form.TargetYear} onChange={(e) => set("TargetYear", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Reduction %</label>
              <input className="input" type="number" min={0} max={100} step={0.1} placeholder="50"
                value={form.ReductionPercent} onChange={(e) => set("ReductionPercent", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label mb-1">Baseline emissions (tCO₂e) <span className="font-normal text-surface-400">optional</span></label>
            <input className="input" type="number" step="any" placeholder="e.g. 12500"
              value={form.BaselineEmissionsTonnes} onChange={(e) => set("BaselineEmissionsTonnes", e.target.value)} />
            <p className="mt-1 text-xs text-surface-400">Used for milestone progress bars. Populated from verified inventory automatically.</p>
          </div>
          <div>
            <label className="label mb-1">Notes <span className="font-normal text-surface-400">optional</span></label>
            <textarea className="input resize-y min-h-[70px]" rows={2}
              value={form.Notes} onChange={(e) => set("Notes", e.target.value)} />
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Creating…" : "Create target"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function TargetsPage() {
  const { activeEntityId } = useAuthStore();
  const [showCreate, setShowCreate] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: Target[] }>({
    queryKey: ["targets", activeEntityId],
    queryFn: () => axiosInstance.get("/api/targets/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const targets = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Targets</h1>
          <p className="page-subtitle">Project goals and annual milestone tracking.</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" /> New target
        </button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : targets.length === 0 ? (
          <div className="p-6 text-sm text-surface-500">
            No targets yet.{" "}
            <button className="text-brand-600 hover:underline" onClick={() => setShowCreate(true)}>
              Set your first reduction target →
            </button>
          </div>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th className="w-8" />
                <th>Target</th>
                <th>Type</th>
                <th>Period</th>
                <th>Reduction</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((t) => {
                const isOpen = expanded === t.TargetId;
                const vl = VALIDATION_LABELS[t.ValidationStatus] ?? VALIDATION_LABELS[1];
                return (
                  <>
                    <tr
                      key={t.TargetId}
                      className="cursor-pointer hover:bg-surface-50"
                      onClick={() => setExpanded(isOpen ? null : t.TargetId)}
                    >
                      <td className="pl-4 pr-1">
                        {isOpen
                          ? <ChevronDown className="h-4 w-4 text-surface-400" />
                          : <ChevronRight className="h-4 w-4 text-surface-400" />}
                      </td>
                      <td className="font-medium text-surface-900">{t.TargetName}</td>
                      <td>
                        <span className="badge badge-slate text-xs">
                          {TARGET_TYPE_LABELS[t.TargetType] ?? t.TargetType}
                        </span>
                      </td>
                      <td className="text-surface-600 text-sm tabular-nums">
                        {t.BaselineYear} → {t.TargetYear}
                      </td>
                      <td className="text-surface-800 font-semibold">
                        {t.ReductionPercent ? (
                          <span className="flex items-center gap-1">
                            <TrendingDown className="h-4 w-4 text-brand-600" />
                            {parseFloat(t.ReductionPercent).toFixed(1)}%
                          </span>
                        ) : "—"}
                      </td>
                      <td><span className={`badge ${vl.badge} text-xs`}>{vl.label}</span></td>
                    </tr>
                    {isOpen && (
                      <MilestonesRow target={t} headers={headers} />
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && activeEntityId && (
        <CreateTargetModal entityId={activeEntityId} onClose={() => setShowCreate(false)} />
      )}
    </div>
  );
}

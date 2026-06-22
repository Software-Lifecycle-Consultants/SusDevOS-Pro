"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";

interface EmissionsSummary {
  scope1_tonnes:            number;
  scope2_location_tonnes:   number;
  scope2_market_tonnes:     number;
  scope3_tonnes:            number;
}

interface EmissionsRecord {
  EmissionsId:          number;
  Title:                string;
  Scope:                number;
  EmissionsAmountTonnes: string | null;
  VerificationStatus:   number;
  Status:               number;
}

interface Project {
  ProjectId:   number;
  ProjectName: string;
  Status:      number;
  phase_count: number;
}

const VERIFICATION_LABELS: Record<number, string> = {
  1: "Unverified", 2: "Pending", 3: "Verified", 4: "Verified (3rd Party)", 5: "CDP Submitted",
};

function ScopeCard({ label, value, colour }: { label: string; value: number; colour: string }) {
  return (
    <div className="card p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-surface-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${colour}`}>
        {value.toFixed(2)}
        <span className="ml-1 text-sm font-normal text-surface-400">tCO₂e</span>
      </p>
    </div>
  );
}

function VerificationBadge({ status }: { status: number }) {
  const colours: Record<number, string> = {
    1: "badge-slate", 2: "badge-yellow", 3: "badge-green", 4: "badge-green", 5: "badge-blue",
  };
  return (
    <span className={`badge ${colours[status] ?? "badge-slate"}`}>
      {VERIFICATION_LABELS[status] ?? "Unknown"}
    </span>
  );
}

export default function DashboardPage() {
  const { user, activeEntityId } = useAuthStore();

  const entityHeader = activeEntityId
    ? { "X-Entity-ID": String(activeEntityId) }
    : {};

  const { data: projects, isLoading: projLoading } = useQuery({
    queryKey: ["projects", activeEntityId],
    queryFn: () =>
      axiosInstance
        .get<{ results: Project[] }>("/api/projects/", { headers: entityHeader })
        .then((r) => r.data.results),
    enabled: !!activeEntityId,
  });

  const { data: emissions, isLoading: emLoading } = useQuery({
    queryKey: ["emissions", activeEntityId],
    queryFn: () =>
      axiosInstance
        .get<{ results: EmissionsRecord[] }>("/api/emissions/", { headers: entityHeader })
        .then((r) => r.data.results),
    enabled: !!activeEntityId,
  });

  // Compute scope totals from emissions list
  const summary: EmissionsSummary = (emissions ?? []).reduce(
    (acc, r) => {
      const t = parseFloat(r.EmissionsAmountTonnes ?? "0");
      if (r.Scope === 1) acc.scope1_tonnes += t;
      if (r.Scope === 2) acc.scope2_location_tonnes += t;
      if (r.Scope === 3) acc.scope3_tonnes += t;
      return acc;
    },
    { scope1_tonnes: 0, scope2_location_tonnes: 0, scope2_market_tonnes: 0, scope3_tonnes: 0 }
  );

  const totalTonnes =
    summary.scope1_tonnes + summary.scope2_location_tonnes + summary.scope3_tonnes;

  const recentEmissions = (emissions ?? []).slice(0, 8);
  const activeProjects  = (projects  ?? []).filter((p) => p.Status === 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          GHG reporting overview
          {user?.IsSuperAdmin && (
            <span className="ml-2 badge badge-blue">SuperAdmin</span>
          )}
        </p>
      </div>

      {/* Scope summary cards */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-surface-700">Emissions Summary (tCO₂e)</h2>
        {!activeEntityId ? (
          <p className="text-sm text-surface-500">
            No entity selected. Use the admin to create an entity and set it as your default.
          </p>
        ) : emLoading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card h-20 animate-pulse bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
            <ScopeCard label="Scope 1"   value={summary.scope1_tonnes}          colour="text-surface-800" />
            <ScopeCard label="Scope 2"   value={summary.scope2_location_tonnes} colour="text-surface-800" />
            <ScopeCard label="Scope 3"   value={summary.scope3_tonnes}          colour="text-surface-800" />
            <div className="card col-span-2 p-5 sm:col-span-2">
              <p className="text-xs font-medium uppercase tracking-wide text-surface-500">Total</p>
              <p className="mt-1 text-2xl font-semibold text-brand-700">
                {totalTonnes.toFixed(2)}
                <span className="ml-1 text-sm font-normal text-surface-400">tCO₂e</span>
              </p>
              <p className="mt-1 text-xs text-surface-400">
                {emissions?.length ?? 0} record{emissions?.length !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
        )}
      </section>

      {/* Two-column: recent emissions + active projects */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* Recent emissions */}
        <section className="card overflow-hidden">
          <div className="border-b border-surface-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-surface-800">Recent Emissions Records</h2>
          </div>
          {emLoading ? (
            <div className="p-4 text-sm text-surface-500">Loading…</div>
          ) : recentEmissions.length === 0 ? (
            <div className="p-4 text-sm text-surface-500">
              No emissions records yet.{" "}
              <a href="/emissions" className="text-brand-600 hover:underline">
                Add your first record →
              </a>
            </div>
          ) : (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Scope</th>
                  <th className="text-right">tCO₂e</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentEmissions.map((r) => (
                  <tr key={r.EmissionsId}>
                    <td className="max-w-[180px] truncate font-medium">{r.Title}</td>
                    <td>
                      <span className="badge badge-slate">Scope {r.Scope}</span>
                    </td>
                    <td className="text-right tabular-nums">
                      {r.EmissionsAmountTonnes
                        ? parseFloat(r.EmissionsAmountTonnes).toFixed(3)
                        : "—"}
                    </td>
                    <td>
                      <VerificationBadge status={r.VerificationStatus} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        {/* Active projects */}
        <section className="card overflow-hidden">
          <div className="border-b border-surface-100 px-4 py-3">
            <h2 className="text-sm font-semibold text-surface-800">Active Projects</h2>
          </div>
          {projLoading ? (
            <div className="p-4 text-sm text-surface-500">Loading…</div>
          ) : activeProjects.length === 0 ? (
            <div className="p-4 text-sm text-surface-500">
              No active projects.{" "}
              <a href="/projects" className="text-brand-600 hover:underline">
                Create a project →
              </a>
            </div>
          ) : (
            <ul className="divide-y divide-surface-100">
              {activeProjects.slice(0, 8).map((p) => (
                <li key={p.ProjectId} className="flex items-center justify-between px-4 py-3">
                  <span className="text-sm font-medium text-surface-800 truncate">
                    {p.ProjectName}
                  </span>
                  <span className="ml-3 shrink-0 text-xs text-surface-400">
                    {p.phase_count} phase{p.phase_count !== 1 ? "s" : ""}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

      </div>
    </div>
  );
}

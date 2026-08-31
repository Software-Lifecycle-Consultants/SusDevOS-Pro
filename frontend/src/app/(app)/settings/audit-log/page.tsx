"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Shield, Download } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface AuditEntry {
  LogId:             number;
  Action:            string;
  TableName:         string;
  RecordId:          number | null;
  Description:       string;
  ChangedByUsername: string;
  ChangedOn:         string;
  RetentionTier:     number;
}

const ACTION_COLOURS: Record<string, string> = {
  Create:          "badge-green",
  Update:          "badge-blue",
  Delete:          "badge-red",
  Unlock_Verified: "badge-red",
  Verify:          "badge-green",
  Login:           "badge-slate",
  Logout:          "badge-slate",
  LoginFailed:     "badge-red",
  PasswordReset:   "badge-yellow",
  Export:          "badge-blue",
  BulkImport:      "badge-blue",
  ReportGenerated: "badge-blue",
  AccessDenied:    "badge-red",
};

const RETENTION_LABELS: Record<number, string> = {
  1: "30 days",
  2: "1 year",
  3: "7 years",
};

const DAYS_OPTIONS = [
  { value: "7",   label: "Last 7 days"  },
  { value: "30",  label: "Last 30 days" },
  { value: "90",  label: "Last 90 days" },
  { value: "365", label: "Last year"    },
  { value: "",    label: "All time"     },
];

const ALL_ACTIONS = [
  "Create","Update","Delete","Verify","Unlock_Verified",
  "Login","Logout","LoginFailed","PasswordReset","Export",
  "BulkImport","ReportGenerated","AccessDenied",
];

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days  = Math.floor(hours / 24);
  if (days > 1)  return `${days}d ago`;
  if (hours > 1) return `${hours}h ago`;
  if (mins > 1)  return `${mins}m ago`;
  return "just now";
}

export default function AuditLogPage() {
  const { activeEntityId, user } = useAuthStore();
  const [days,   setDays]   = useState("30");
  const [action, setAction] = useState("");

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: AuditEntry[]; count: number }>({
    queryKey: ["audit-log", activeEntityId, days, action],
    queryFn: () => {
      const params = new URLSearchParams();
      if (days)   params.set("days",   days);
      if (action) params.set("action", action);
      return axiosInstance.get(`/api/shared/audit-log/?${params}`, { headers }).then((r) => r.data);
    },
    enabled: !!activeEntityId,
  });

  const entries = data?.results ?? [];

  function exportCSV() {
    const header = "LogId,Action,Table,RecordId,Description,ChangedBy,ChangedOn,Retention\n";
    const rows = entries.map((e) =>
      [e.LogId, e.Action, e.TableName ?? "", e.RecordId ?? "", `"${(e.Description ?? "").replace(/"/g, "'")}"`,
       e.ChangedByUsername, e.ChangedOn, RETENTION_LABELS[e.RetentionTier] ?? ""].join(",")
    ).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (!user) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-surface-400" />
          <div>
            <p className="text-sm font-semibold text-surface-800">{data?.count ?? 0} entries</p>
            <p className="text-xs text-surface-400">Admin-only · read-only · append-only trail</p>
          </div>
        </div>
        <button className="btn-secondary btn-sm flex items-center gap-1.5" onClick={exportCSV}
          disabled={entries.length === 0}>
          <Download className="h-4 w-4" /> Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div>
          <label className="label mb-1">Period</label>
          <select className="input h-9 text-sm" value={days} onChange={(e) => setDays(e.target.value)}>
            {DAYS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label mb-1">Action</label>
          <select className="input h-9 text-sm" value={action} onChange={(e) => setAction(e.target.value)}>
            <option value="">All actions</option>
            {ALL_ACTIONS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : entries.length === 0 ? (
          <div className="p-8 text-center">
            <Shield className="h-8 w-8 text-surface-300 mx-auto mb-3" />
            <p className="text-sm text-surface-500">No audit log entries for this filter.</p>
            <p className="text-xs text-surface-400 mt-1">
              Entries are created on significant actions: logins, data changes, verifications, unlocks and exports.
            </p>
          </div>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Action</th>
                <th>Table / record</th>
                <th>Description</th>
                <th>User</th>
                <th>When</th>
                <th>Retention</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.LogId}>
                  <td>
                    <span className={`badge text-xs ${ACTION_COLOURS[e.Action] ?? "badge-slate"}`}>
                      {e.Action}
                    </span>
                  </td>
                  <td className="text-surface-500 text-xs">
                    {e.TableName
                      ? <span>{e.TableName}{e.RecordId ? <span className="text-surface-400"> #{e.RecordId}</span> : ""}</span>
                      : "—"}
                  </td>
                  <td className="text-surface-600 text-sm max-w-[280px] truncate" title={e.Description ?? ""}>
                    {e.Description ?? "—"}
                  </td>
                  <td className="text-surface-600 text-sm">{e.ChangedByUsername}</td>
                  <td className="text-surface-400 text-xs whitespace-nowrap" title={e.ChangedOn}>
                    {timeAgo(e.ChangedOn)}
                  </td>
                  <td>
                    <span className={`text-xs ${e.RetentionTier === 3 ? "text-brand-600 font-medium" : "text-surface-400"}`}>
                      {RETENTION_LABELS[e.RetentionTier] ?? "—"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-surface-400">
        Showing up to 500 most recent entries. Retention periods: 30-day (session events) ·
        1-year (standard changes) · 7-year (regulatory actions: verifications, unlocks, exports).
        Purged automatically by the nightly Celery task.
      </p>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";
import { EmptyState } from "@/components/EmptyState";

interface ReportJob {
  ReportJobId:  number;
  ReportType:   string;
  Format:       string;
  JobStatus:    number;
  status_label: string;
  QueuedAt:     string;
  CompletedAt:  string | null;
  ErrorMessage: string | null;
  FileSizeBytes: number | null;
}

const STATUS_STYLES: Record<number, string> = {
  1: "badge-slate",  // Queued
  2: "badge-yellow", // Processing
  3: "badge-green",  // Complete
  4: "badge-red",    // Failed
};

const TYPE_LABELS: Record<string, string> = {
  emissions_summary: "Emissions Summary",
  ghg_inventory:     "GHG Inventory",
  phase_progress:    "Phase Progress",
  tree_log:          "Tree & Restoration Log",
};

export default function ReportsPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const [showQueue, setShowQueue] = useState(false);
  const [queueForm, setQueueForm] = useState({
    ReportType: "emissions_summary",
    Format:     "pdf",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["reports", activeEntityId],
    queryFn: () =>
      axiosInstance
        .get<{ results: ReportJob[] }>("/api/reports/", {
          headers: activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {},
        })
        .then((r) => r.data),
    enabled: !!activeEntityId,
    refetchInterval: (q) => {
      // Poll every 5 s while any job is Queued or Processing
      const processing = q.state.data?.results?.some((j) => j.JobStatus <= 2);
      return processing ? 5000 : false;
    },
  });

  const queue = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      axiosInstance.post("/api/reports/", data, {
        headers: { "X-Entity-ID": String(activeEntityId) },
      }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports", activeEntityId] });
      setShowQueue(false);
    },
  });

  const download = useMutation({
    mutationFn: (id: number) =>
      axiosInstance.get(`/api/reports/${id}/download/`, {
        headers: { "X-Entity-ID": String(activeEntityId) },
      }).then((r) => r.data),
    onSuccess: (data) => {
      if (data.download_url) window.open(data.download_url, "_blank");
    },
  });

  const jobs = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Queue and download generated reports</p>
        </div>
        <button className="btn-primary" onClick={() => setShowQueue(true)}>
          + Generate report
        </button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : jobs.length === 0 ? (
          <EmptyState
            message="No reports yet. Generate your first GHG inventory report."
            action={{ label: "+ Generate report", href: "#" }}
          />
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Type</th>
                <th>Format</th>
                <th>Status</th>
                <th>Queued</th>
                <th>Completed</th>
                <th>Size</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.ReportJobId}>
                  <td className="font-medium">{TYPE_LABELS[j.ReportType] ?? j.ReportType}</td>
                  <td className="uppercase text-surface-500">{j.Format}</td>
                  <td>
                    <span className={`badge ${STATUS_STYLES[j.JobStatus] ?? "badge-slate"}`}>
                      {j.status_label}
                    </span>
                  </td>
                  <td className="text-surface-500 text-xs">
                    {new Date(j.QueuedAt).toLocaleString()}
                  </td>
                  <td className="text-surface-500 text-xs">
                    {j.CompletedAt ? new Date(j.CompletedAt).toLocaleString() : "—"}
                  </td>
                  <td className="text-surface-500 text-xs">
                    {j.FileSizeBytes ? `${Math.round(j.FileSizeBytes / 1024)} KB` : "—"}
                  </td>
                  <td>
                    {j.JobStatus === 3 && (
                      <button
                        className="btn-ghost btn-sm"
                        onClick={() => download.mutate(j.ReportJobId)}
                        disabled={download.isPending}
                      >
                        Download
                      </button>
                    )}
                    {j.JobStatus === 4 && (
                      <span className="text-xs text-red-500" title={j.ErrorMessage ?? ""}>
                        Failed
                      </span>
                    )}
                    {j.JobStatus <= 2 && (
                      <span className="text-xs text-surface-400 animate-pulse">Processing…</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Queue modal */}
      {showQueue && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="card w-full max-w-md p-6">
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-base font-semibold">Generate report</h2>
              <button onClick={() => setShowQueue(false)} className="btn-ghost btn-sm">✕</button>
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                queue.mutate({
                  ReportType: queueForm.ReportType,
                  Format:     queueForm.Format,
                  Parameters: {},
                });
              }}
              className="space-y-4"
            >
              <div>
                <label className="label mb-1">Report type</label>
                <select className="input" value={queueForm.ReportType}
                  onChange={(e) => setQueueForm((f) => ({ ...f, ReportType: e.target.value }))}>
                  {Object.entries(TYPE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label mb-1">Format</label>
                <select className="input" value={queueForm.Format}
                  onChange={(e) => setQueueForm((f) => ({ ...f, Format: e.target.value }))}>
                  <option value="pdf">PDF</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowQueue(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={queue.isPending} className="btn-primary">
                  {queue.isPending ? "Queuing…" : "Queue report"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

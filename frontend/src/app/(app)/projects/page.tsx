"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";
import { EmptyState } from "@/components/EmptyState";

interface Project {
  ProjectId:   number;
  ProjectName: string;
  ProjectType: string;
  Country:     string;
  StartDate:   string | null;
  EndDate:     string | null;
  Status:      number;
  phase_count: number;
}

function CreateProjectModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    ProjectName: "", ProjectType: "Residential",
    Country: "United Kingdom", StartDate: "", EndDate: "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      axiosInstance.post("/api/projects/", data, {
        headers: { "X-Entity-ID": String(entityId) },
      }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Failed to create project.");
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-md p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold">New project</h2>
          <button onClick={onClose} className="btn-ghost btn-sm">✕</button>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate({
              ProjectName: form.ProjectName,
              ProjectType: form.ProjectType,
              Country:     form.Country,
              StartDate:   form.StartDate || null,
              EndDate:     form.EndDate || null,
            });
          }}
          className="space-y-4"
        >
          <div>
            <label className="label mb-1">Project name</label>
            <input className="input" required value={form.ProjectName}
              onChange={(e) => setForm((f) => ({ ...f, ProjectName: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Type</label>
              <select className="input" value={form.ProjectType}
                onChange={(e) => setForm((f) => ({ ...f, ProjectType: e.target.value }))}>
                {["Residential","Commercial","Mixed Use","Industrial","Infrastructure","Other"]
                  .map((t) => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label mb-1">Country</label>
              <input className="input" value={form.Country}
                onChange={(e) => setForm((f) => ({ ...f, Country: e.target.value }))} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">Start date</label>
              <input className="input" type="date" value={form.StartDate}
                onChange={(e) => setForm((f) => ({ ...f, StartDate: e.target.value }))} />
            </div>
            <div>
              <label className="label mb-1">End date</label>
              <input className="input" type="date" value={form.EndDate}
                onChange={(e) => setForm((f) => ({ ...f, EndDate: e.target.value }))} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Saving…" : "Create project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ProjectsPage() {
  const { activeEntityId } = useAuthStore();
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["projects", activeEntityId],
    queryFn: () =>
      axiosInstance
        .get<{ results: Project[]; count: number }>("/api/projects/", {
          headers: activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {},
        })
        .then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const projects = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">{data?.count ?? 0} development projects</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + New project
        </button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : projects.length === 0 ? (
          <EmptyState
            message="No projects yet. Create your first project to start tracking emissions."
            action={{ label: "+ New project", onClick: () => setShowCreate(true) }}
          />
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Country</th>
                <th>Start</th>
                <th>End</th>
                <th>Phases</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.ProjectId}>
                  <td className="font-medium">
                    <Link href={`/projects/${p.ProjectId}`} className="text-brand-700 hover:underline">{p.ProjectName}</Link>
                  </td>
                  <td className="text-surface-500">{p.ProjectType ?? "—"}</td>
                  <td className="text-surface-500">{p.Country ?? "—"}</td>
                  <td className="text-surface-500">{p.StartDate ?? "—"}</td>
                  <td className="text-surface-500">{p.EndDate ?? "—"}</td>
                  <td className="tabular-nums text-center">{p.phase_count}</td>
                  <td>
                    <span className={`badge ${p.Status === 1 ? "badge-green" : "badge-slate"}`}>
                      {p.Status === 1 ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && activeEntityId && (
        <CreateProjectModal entityId={activeEntityId} onClose={() => setShowCreate(false)} />
      )}
    </div>
  );
}

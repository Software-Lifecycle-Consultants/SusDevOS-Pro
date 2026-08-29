"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { DetailView, type DetailField } from "@/components/DetailView";

const fields: DetailField[] = [
  { key: "ProjectName", label: "Project name" },
  { key: "ProjectReference", label: "Reference" },
  { key: "ProjectType", label: "Type" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "StartDate", label: "Start date", type: "date" },
  { key: "EndDate", label: "End date", type: "date" },
  { key: "Location", label: "Location" },
  { key: "Country", label: "Country" },
  { key: "TotalAreaHectares", label: "Area (ha)", type: "number" },
  { key: "EstimatedValueGBP", label: "Estimated value (GBP)", type: "number" },
];

interface ProjectPhase {
  PhaseId: number;
  PhaseName: string;
  PhaseNumber: number | null;
  Description: string | null;
  StartDate: string | null;
  EndDate: string | null;
  TargetEmissionsTonnes: string | null;
}

interface PhaseForm {
  PhaseName: string;
  PhaseNumber: string;
  Description: string;
  StartDate: string;
  EndDate: string;
  TargetEmissionsTonnes: string;
}

const emptyPhaseForm = (): PhaseForm => ({
  PhaseName: "",
  PhaseNumber: "",
  Description: "",
  StartDate: "",
  EndDate: "",
  TargetEmissionsTonnes: "",
});

function errorMessage(error: unknown, fallback: string) {
  const data = (
    error as {
      response?: {
        data?: { detail?: string; errors?: Record<string, string[]> };
      };
    }
  )?.response?.data;
  return data?.errors
    ? (Object.values(data.errors)[0]?.[0] ?? fallback)
    : (data?.detail ?? fallback);
}

function ProjectPhasesPanel({ projectId }: { projectId: string }) {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const headers = activeEntityId
    ? { "X-Entity-ID": String(activeEntityId) }
    : {};
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<PhaseForm>(emptyPhaseForm);
  const [error, setError] = useState<string | null>(null);

  const { data: phases = [], isLoading } = useQuery<ProjectPhase[]>({
    queryKey: ["project-phases", projectId, activeEntityId],
    queryFn: () =>
      axiosInstance
        .get(`/api/projects/${projectId}/phases/`, { headers })
        .then((response) => response.data),
    enabled: Boolean(activeEntityId),
  });

  const save = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editingId === null
        ? axiosInstance.post(`/api/projects/${projectId}/phases/`, payload, { headers })
        : axiosInstance.patch(
            `/api/projects/${projectId}/phases/${editingId}/`,
            payload,
            { headers },
          ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["project-phases", projectId, activeEntityId],
      });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setForm(emptyPhaseForm());
      setEditingId(null);
      setShowForm(false);
      setError(null);
    },
    onError: (err) => setError(errorMessage(err, "Failed to save phase.")),
  });

  const remove = useMutation({
    mutationFn: (phaseId: number) =>
      axiosInstance.delete(`/api/projects/${projectId}/phases/${phaseId}/`, {
        headers,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["project-phases", projectId, activeEntityId],
      });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setError(null);
    },
    onError: (err) => setError(errorMessage(err, "Failed to remove phase.")),
  });

  function beginEdit(phase: ProjectPhase) {
    setEditingId(phase.PhaseId);
    setForm({
      PhaseName: phase.PhaseName,
      PhaseNumber: phase.PhaseNumber === null ? "" : String(phase.PhaseNumber),
      Description: phase.Description ?? "",
      StartDate: phase.StartDate ?? "",
      EndDate: phase.EndDate ?? "",
      TargetEmissionsTonnes: phase.TargetEmissionsTonnes ?? "",
    });
    setShowForm(true);
    setError(null);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
    setForm(emptyPhaseForm());
    setError(null);
  }

  return (
    <section className="card p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-surface-900">Project phases</h2>
          <p className="mt-1 text-sm text-surface-500">
            Use phases only where they help group real project work and emissions.
          </p>
        </div>
        {!showForm && (
          <button
            className="btn-primary"
            onClick={() => {
              setForm(emptyPhaseForm());
              setEditingId(null);
              setShowForm(true);
            }}
          >
            + Add phase
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {showForm && (
        <form
          className="mt-5 space-y-4 border-t border-surface-100 pt-5"
          onSubmit={(event) => {
            event.preventDefault();
            save.mutate({
              PhaseName: form.PhaseName,
              PhaseNumber: form.PhaseNumber ? Number(form.PhaseNumber) : null,
              Description: form.Description || null,
              StartDate: form.StartDate || null,
              EndDate: form.EndDate || null,
              TargetEmissionsTonnes: form.TargetEmissionsTonnes || null,
            });
          }}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label mb-1">Phase name</label>
              <input
                className="input"
                required
                value={form.PhaseName}
                onChange={(event) =>
                  setForm((current) => ({ ...current, PhaseName: event.target.value }))
                }
              />
            </div>
            <div>
              <label className="label mb-1">Sequence number</label>
              <input
                className="input"
                type="number"
                min={1}
                value={form.PhaseNumber}
                onChange={(event) =>
                  setForm((current) => ({ ...current, PhaseNumber: event.target.value }))
                }
              />
            </div>
            <div>
              <label className="label mb-1">Start date</label>
              <input
                className="input"
                type="date"
                value={form.StartDate}
                onChange={(event) =>
                  setForm((current) => ({ ...current, StartDate: event.target.value }))
                }
              />
            </div>
            <div>
              <label className="label mb-1">End date</label>
              <input
                className="input"
                type="date"
                value={form.EndDate}
                onChange={(event) =>
                  setForm((current) => ({ ...current, EndDate: event.target.value }))
                }
              />
            </div>
            <div>
              <label className="label mb-1">Target emissions (tCO₂e)</label>
              <input
                className="input"
                type="number"
                min={0}
                step="any"
                value={form.TargetEmissionsTonnes}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    TargetEmissionsTonnes: event.target.value,
                  }))
                }
              />
            </div>
          </div>
          <div>
            <label className="label mb-1">Description</label>
            <textarea
              className="input min-h-[72px] resize-y"
              value={form.Description}
              onChange={(event) =>
                setForm((current) => ({ ...current, Description: event.target.value }))
              }
            />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" disabled={save.isPending} type="submit">
              {save.isPending
                ? "Saving…"
                : editingId === null
                  ? "Create phase"
                  : "Save phase"}
            </button>
            <button className="btn-secondary" type="button" onClick={cancelForm}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="mt-5 overflow-x-auto border-t border-surface-100 pt-5">
        {isLoading ? (
          <p className="text-sm text-surface-500">Loading phases…</p>
        ) : phases.length === 0 ? (
          <p className="text-sm text-surface-500">No phases. Records can still be linked directly to the project.</p>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>#</th>
                <th>Phase</th>
                <th>Period</th>
                <th className="text-right">Target tCO₂e</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {phases.map((phase) => (
                <tr key={phase.PhaseId}>
                  <td className="text-surface-500">{phase.PhaseNumber ?? "—"}</td>
                  <td>
                    <div className="font-medium text-surface-800">{phase.PhaseName}</div>
                    {phase.Description && (
                      <div className="mt-0.5 max-w-md truncate text-xs text-surface-400">
                        {phase.Description}
                      </div>
                    )}
                  </td>
                  <td className="text-surface-500">
                    {phase.StartDate || phase.EndDate
                      ? `${phase.StartDate ?? "…"} – ${phase.EndDate ?? "…"}`
                      : "—"}
                  </td>
                  <td className="text-right tabular-nums">
                    {phase.TargetEmissionsTonnes ?? "—"}
                  </td>
                  <td>
                    <div className="flex justify-end gap-2">
                      <button className="btn-ghost btn-sm" onClick={() => beginEdit(phase)}>
                        Edit
                      </button>
                      <button
                        className="btn-ghost btn-sm text-red-600"
                        disabled={remove.isPending}
                        onClick={() => {
                          if (window.confirm(`Remove phase “${phase.PhaseName}”?`)) {
                            remove.mutate(phase.PhaseId);
                          }
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <div className="space-y-4">
      <DetailView
        resourcePath="/api/projects/"
        id={id}
        queryKey="projects"
        listHref="/projects"
        title={(record) => String(record.ProjectName ?? "Project")}
        subtitle={(record) => [record.ProjectType, record.Country].filter(Boolean).join(" · ")}
        fields={fields}
      />
      <ProjectPhasesPanel projectId={id} />
    </div>
  );
}

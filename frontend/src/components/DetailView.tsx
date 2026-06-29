"use client";

/**
 * Generic detail + inline-edit view for a tenant-scoped resource.
 *
 * Field-config driven so each resource's [id] page stays small. Fetches
 * `${resourcePath}${id}/`, renders read-only fields, toggles to an edit form
 * (PATCH), supports delete, and optional custom actions (e.g. verify/unlock).
 */
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";

type Row = Record<string, unknown>;

export interface DetailField {
  key: string;
  label: string;
  type?: "text" | "number" | "textarea" | "date" | "select" | "checkbox";
  options?: { value: string | number; label: string }[];
  editable?: boolean; // default true
  render?: (value: unknown, row: Row) => React.ReactNode; // custom read-only render
  help?: string;
}

export interface DetailAction {
  label: string;
  /** Returns a request to run, or performs navigation itself. */
  run: (row: Row, headers: Record<string, string>) => Promise<unknown>;
  show?: (row: Row) => boolean;
  variant?: "secondary" | "danger";
  confirm?: string;
  /** Prompt the user for a string and pass it to run via row.__prompt. */
  prompt?: string;
}

interface DetailViewProps {
  resourcePath: string; // e.g. "/api/emissions/"
  id: string;
  title: (row: Row) => string;
  subtitle?: (row: Row) => string;
  fields: DetailField[];
  listHref: string;
  queryKey: string;
  canEdit?: (row: Row) => boolean;
  canDelete?: (row: Row) => boolean;
  actions?: DetailAction[];
}

function str(v: unknown): string {
  if (v === null || v === undefined) return "";
  return String(v);
}

export function DetailView(props: DetailViewProps) {
  const { resourcePath, id, fields, listHref, queryKey } = props;
  const router = useRouter();
  const queryClient = useQueryClient();
  const { activeEntityId } = useAuthStore();
  const headers = useMemo<Record<string, string>>(
    () =>
      activeEntityId
        ? { "X-Entity-ID": String(activeEntityId) }
        : ({} as Record<string, string>),
    [activeEntityId],
  );

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const {
    data: row,
    isLoading,
    refetch,
  } = useQuery<Row>({
    queryKey: [queryKey, id, activeEntityId],
    queryFn: () =>
      axiosInstance
        .get(`${resourcePath}${id}/`, { headers })
        .then((r) => r.data),
    enabled: !!activeEntityId,
  });

  useEffect(() => {
    if (row && editing) {
      const init: Record<string, string> = {};
      for (const f of fields)
        if (f.editable !== false) init[f.key] = str(row[f.key]);
      setForm(init);
    }
  }, [row, editing, fields]);

  const save = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      axiosInstance
        .patch(`${resourcePath}${id}/`, payload, { headers })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      setEditing(false);
      setError(null);
      refetch();
    },
    onError: (err: unknown) => {
      const d = (
        err as {
          response?: {
            data?: { detail?: string; errors?: Record<string, string[]> };
          };
        }
      )?.response?.data;
      setError(
        d?.errors
          ? (Object.values(d.errors)[0]?.[0] ?? "Validation error.")
          : (d?.detail ?? "Save failed."),
      );
    },
  });

  const del = useMutation({
    mutationFn: () =>
      axiosInstance.delete(`${resourcePath}${id}/`, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      router.push(listHref);
    },
    onError: () => setError("Delete failed."),
  });

  const action = useMutation({
    mutationFn: (fn: () => Promise<unknown>) => fn(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      refetch();
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { detail?: string } } })?.response
        ?.data;
      setError(d?.detail ?? "Action failed.");
    },
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const payload: Record<string, unknown> = {};
    for (const f of fields) {
      if (f.editable === false) continue;
      const v = form[f.key];
      if (f.type === "number") payload[f.key] = v === "" ? null : Number(v);
      else if (f.type === "checkbox") payload[f.key] = v === "true";
      else payload[f.key] = v === "" ? null : v;
    }
    save.mutate(payload);
  }

  if (!activeEntityId)
    return (
      <p className="p-6 text-sm text-surface-500">Select an entity first.</p>
    );
  if (isLoading)
    return <p className="p-6 text-sm text-surface-500">Loading…</p>;
  if (!row) return <p className="p-6 text-sm text-surface-500">Not found.</p>;

  const canEdit = props.canEdit ? props.canEdit(row) : true;
  const canDelete = props.canDelete ? props.canDelete(row) : true;

  return (
    <div className="space-y-4">
      <Link
        href={listHref}
        className="inline-flex items-center gap-1 text-sm text-surface-500 hover:text-surface-700"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="page-title">{props.title(row)}</h1>
          {props.subtitle && (
            <p className="page-subtitle">{props.subtitle(row)}</p>
          )}
        </div>
        <div className="flex gap-2">
          {props.actions
            ?.filter((a) => !a.show || a.show(row))
            .map((a) => (
              <button
                key={a.label}
                className={
                  a.variant === "danger"
                    ? "btn-secondary text-red-600"
                    : "btn-secondary"
                }
                disabled={action.isPending}
                onClick={() => {
                  if (a.confirm && !window.confirm(a.confirm)) return;
                  let r = row;
                  if (a.prompt) {
                    const input = window.prompt(a.prompt);
                    if (input === null) return;
                    r = { ...row, __prompt: input };
                  }
                  action.mutate(() => a.run(r, headers));
                }}
              >
                {a.label}
              </button>
            ))}
          {!editing && canEdit && (
            <button className="btn-primary" onClick={() => setEditing(true)}>
              Edit
            </button>
          )}
          {!editing && canDelete && (
            <button
              className="btn-secondary text-red-600"
              disabled={del.isPending}
              onClick={() => {
                if (window.confirm("Delete this record?")) del.mutate();
              }}
            >
              Delete
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="card p-6">
        {editing ? (
          <form onSubmit={submit} className="space-y-4">
            {fields
              .filter((f) => f.editable !== false)
              .map((f) => (
                <div key={f.key}>
                  <label className="label mb-1">{f.label}</label>
                  {f.type === "textarea" ? (
                    <textarea
                      className="input resize-y min-h-[72px]"
                      value={form[f.key] ?? ""}
                      onChange={(e) =>
                        setForm((s) => ({ ...s, [f.key]: e.target.value }))
                      }
                    />
                  ) : f.type === "select" ? (
                    <select
                      className="input"
                      value={form[f.key] ?? ""}
                      onChange={(e) =>
                        setForm((s) => ({ ...s, [f.key]: e.target.value }))
                      }
                    >
                      <option value="">— select —</option>
                      {f.options?.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </select>
                  ) : f.type === "checkbox" ? (
                    <select
                      className="input"
                      value={form[f.key] ?? "false"}
                      onChange={(e) =>
                        setForm((s) => ({ ...s, [f.key]: e.target.value }))
                      }
                    >
                      <option value="true">Yes</option>
                      <option value="false">No</option>
                    </select>
                  ) : (
                    <input
                      className="input"
                      type={
                        f.type === "number"
                          ? "number"
                          : f.type === "date"
                            ? "date"
                            : "text"
                      }
                      step={f.type === "number" ? "any" : undefined}
                      value={form[f.key] ?? ""}
                      onChange={(e) =>
                        setForm((s) => ({ ...s, [f.key]: e.target.value }))
                      }
                    />
                  )}
                  {f.help && (
                    <p className="mt-1 text-xs text-surface-400">{f.help}</p>
                  )}
                </div>
              ))}
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setEditing(false);
                  setError(null);
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={save.isPending}
              >
                {save.isPending ? "Saving…" : "Save changes"}
              </button>
            </div>
          </form>
        ) : (
          <dl className="grid grid-cols-1 gap-x-8 gap-y-3 sm:grid-cols-2">
            {fields.map((f) => (
              <div key={f.key}>
                <dt className="text-xs font-medium uppercase tracking-wider text-surface-400">
                  {f.label}
                </dt>
                <dd className="mt-0.5 text-sm text-surface-800">
                  {f.render
                    ? f.render(row[f.key], row)
                    : str(row[f.key]) || "—"}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </div>
  );
}

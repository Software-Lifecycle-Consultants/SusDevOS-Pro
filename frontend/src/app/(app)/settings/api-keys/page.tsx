"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Key, Copy, Check, Trash2, Plus } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface ApiKey {
  ApiKeyId:    number;
  KeyName:     string;
  KeyPrefix:   string;
  CreatedAt:   string;
  LastUsedAt:  string | null;
}

function useCopy(timeout = 2000) {
  const [copied, setCopied] = useState<string | null>(null);
  function copy(text: string, key: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key);
      setTimeout(() => setCopied(null), timeout);
    });
  }
  return { copied, copy };
}

export default function ApiKeysPage() {
  const { activeEntityId } = useAuthStore();
  const queryClient = useQueryClient();
  const { copied, copy } = useCopy();
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: ApiKey[] }>({
    queryKey: ["api-keys", activeEntityId],
    queryFn: () => axiosInstance.get(`/api/entities/${activeEntityId}/api-keys/`, { headers })
      .then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const generate = useMutation({
    mutationFn: () =>
      axiosInstance.post(`/api/entities/${activeEntityId}/api-keys/`, { KeyName: newKeyName }, { headers }),
    onSuccess: (res) => {
      setGeneratedKey(res.data.RawKey);
      setNewKeyName("");
      setShowForm(false);
      queryClient.invalidateQueries({ queryKey: ["api-keys", activeEntityId] });
    },
  });

  const revoke = useMutation({
    mutationFn: (keyId: number) =>
      axiosInstance.delete(`/api/entities/${activeEntityId}/api-keys/${keyId}/`, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys", activeEntityId] }),
  });

  const keys = data?.results ?? [];

  return (
    <div className="space-y-4">
      {/* New key revealed */}
      {generatedKey && (
        <div className="rounded-lg border border-brand-200 bg-brand-50 p-4">
          <p className="text-sm font-semibold text-brand-800 mb-1">
            Copy your new API key — it won&apos;t be shown again.
          </p>
          <div className="flex items-center gap-2 mt-2">
            <code className="flex-1 bg-white border border-brand-200 rounded px-3 py-2 text-sm font-mono text-surface-800 truncate">
              {generatedKey}
            </code>
            <button
              onClick={() => copy(generatedKey, "new")}
              className="btn-secondary shrink-0 flex items-center gap-1.5 btn-sm"
            >
              {copied === "new" ? <Check className="h-4 w-4 text-brand-600" /> : <Copy className="h-4 w-4" />}
              {copied === "new" ? "Copied" : "Copy"}
            </button>
          </div>
          <button className="mt-3 text-xs text-brand-600 hover:underline" onClick={() => setGeneratedKey(null)}>
            I&apos;ve saved it — dismiss
          </button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-sm text-surface-500">{keys.length} key{keys.length !== 1 ? "s" : ""}</p>
        <button className="btn-primary flex items-center gap-2 btn-sm" onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4" /> Generate key
        </button>
      </div>

      {/* Generate form */}
      {showForm && (
        <div className="card p-4 flex items-end gap-3">
          <div className="flex-1">
            <label className="label mb-1">Key name</label>
            <input className="input" placeholder="e.g. Building energy meters"
              value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} />
          </div>
          <button
            className="btn-primary shrink-0"
            disabled={!newKeyName.trim() || generate.isPending}
            onClick={() => generate.mutate()}
          >
            {generate.isPending ? "Generating…" : "Generate"}
          </button>
          <button className="btn-ghost shrink-0" onClick={() => setShowForm(false)}>Cancel</button>
        </div>
      )}

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : keys.length === 0 ? (
          <div className="p-6 flex items-center gap-3 text-sm text-surface-500">
            <Key className="h-5 w-5 text-surface-300" />
            No API keys yet. Generate a key to allow integrations to push data to SusDevOS.
          </div>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th>Created</th>
                <th>Last used</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {keys.map((k) => (
                <tr key={k.ApiKeyId}>
                  <td className="font-medium">{k.KeyName}</td>
                  <td><code className="text-xs bg-surface-100 px-2 py-0.5 rounded">{k.KeyPrefix}…</code></td>
                  <td className="text-surface-500 text-xs">
                    {new Date(k.CreatedAt).toLocaleDateString()}
                  </td>
                  <td className="text-surface-500 text-xs">
                    {k.LastUsedAt ? new Date(k.LastUsedAt).toLocaleDateString() : "Never"}
                  </td>
                  <td className="text-right">
                    <button
                      className="btn-ghost btn-sm text-red-500 hover:text-red-700"
                      onClick={() => { if (confirm("Revoke this key?")) revoke.mutate(k.ApiKeyId); }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

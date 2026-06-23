"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { UserPlus, MoreHorizontal, X } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface User {
  UserId:    number;
  email:     string;
  username:  string;
  FirstName: string | null;
  LastName:  string | null;
  role:      string | null;
  is_active: boolean;
  Status:    number;
}

const ROLE_OPTIONS = [
  { value: "admin",   label: "Admin"   },
  { value: "manager", label: "Manager" },
  { value: "staff",   label: "Staff"   },
];

const ROLE_COLOURS: Record<string, string> = {
  admin:       "badge-blue",
  manager:     "badge-yellow",
  staff:       "badge-slate",
  super_admin: "badge-red",
};

function displayName(u: User) {
  const name = [u.FirstName, u.LastName].filter(Boolean).join(" ");
  return name || u.username;
}

function InviteModal({ onClose, entityId }: { onClose: () => void; entityId: number }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ first_name: "", last_name: "", email: "", role_key: "manager" });
  const [error, setError] = useState<string | null>(null);

  const headers = { "X-Entity-ID": String(entityId) };

  const mutation = useMutation({
    mutationFn: () =>
      axiosInstance.post("/api/users/", {
        email:     form.email,
        username:  form.email.split("@")[0],
        FirstName: form.first_name,
        LastName:  form.last_name,
        role_key:  form.role_key,
      }, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", entityId] });
      onClose();
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      if (data) {
        const first = Object.values(data)[0];
        setError(Array.isArray(first) ? first[0] as string : String(first));
      } else {
        setError("Failed to invite user.");
      }
    },
  });

  function set(k: keyof typeof form, v: string) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="card w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-surface-900">Invite a team member</h2>
          <button onClick={onClose} className="btn-ghost btn-sm"><X className="h-4 w-4" /></button>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label mb-1">First name</label>
              <input className="input" required value={form.first_name}
                onChange={(e) => set("first_name", e.target.value)} />
            </div>
            <div>
              <label className="label mb-1">Last name</label>
              <input className="input" required value={form.last_name}
                onChange={(e) => set("last_name", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label mb-1">Work email</label>
            <input className="input" type="email" required value={form.email}
              onChange={(e) => set("email", e.target.value)} />
          </div>
          <div>
            <label className="label mb-1">Role</label>
            <select className="input" value={form.role_key}
              onChange={(e) => set("role_key", e.target.value)}>
              {ROLE_OPTIONS.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
            <p className="mt-1 text-xs text-surface-400">
              They'll receive an email with a link to set their password.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary">
              {mutation.isPending ? "Sending invite…" : "Send invite"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function UsersPage() {
  const { activeEntityId, user: me } = useAuthStore();
  const queryClient = useQueryClient();
  const [showInvite, setShowInvite] = useState(false);
  const [openMenu, setOpenMenu] = useState<number | null>(null);

  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data, isLoading } = useQuery<{ results: User[] }>({
    queryKey: ["users", activeEntityId],
    queryFn: () => axiosInstance.get("/api/users/", { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  const changeRole = useMutation({
    mutationFn: ({ userId, role_key }: { userId: number; role_key: string }) =>
      axiosInstance.patch(`/api/users/${userId}/role/`, { role_key }, { headers }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users", activeEntityId] }),
  });

  const deactivate = useMutation({
    mutationFn: (userId: number) =>
      axiosInstance.delete(`/api/users/${userId}/`, { headers }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users", activeEntityId] });
      setOpenMenu(null);
    },
  });

  const users = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-surface-500">{users.length} member{users.length !== 1 ? "s" : ""}</p>
        <button className="btn-primary flex items-center gap-2 btn-sm"
          onClick={() => setShowInvite(true)}>
          <UserPlus className="h-4 w-4" />
          Invite user
        </button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-sm text-surface-500">Loading…</div>
        ) : users.length === 0 ? (
          <div className="p-6 text-sm text-surface-500">No users yet. Invite your first team member.</div>
        ) : (
          <table className="table-auto w-full">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.UserId} className="relative">
                  <td className="font-medium">{displayName(u)}</td>
                  <td className="text-surface-500">{u.email}</td>
                  <td>
                    {u.role === "super_admin" ? (
                      <span className={`badge ${ROLE_COLOURS.super_admin}`}>Super Admin</span>
                    ) : (
                      <select
                        className="text-xs border border-surface-200 rounded px-2 py-1 text-surface-700 bg-white"
                        value={u.role ?? ""}
                        disabled={u.UserId === me?.UserId}
                        onChange={(e) => changeRole.mutate({ userId: u.UserId, role_key: e.target.value })}
                      >
                        {ROLE_OPTIONS.map((r) => (
                          <option key={r.value} value={r.value}>{r.label}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td>
                    <span className={`badge ${u.is_active && u.Status !== 4 ? "badge-green" : "badge-slate"}`}>
                      {u.is_active && u.Status !== 4 ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="text-right">
                    {u.UserId !== me?.UserId && u.role !== "super_admin" && (
                      <div className="relative inline-block">
                        <button
                          className="btn-ghost btn-sm p-1"
                          onClick={() => setOpenMenu(openMenu === u.UserId ? null : u.UserId)}
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                        {openMenu === u.UserId && (
                          <div className="absolute right-0 z-10 mt-1 w-36 rounded-lg border border-surface-200 bg-white shadow-lg py-1">
                            <button
                              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                              onClick={() => {
                                if (confirm(`Deactivate ${displayName(u)}?`)) {
                                  deactivate.mutate(u.UserId);
                                }
                              }}
                            >
                              Deactivate
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showInvite && activeEntityId && (
        <InviteModal entityId={activeEntityId} onClose={() => setShowInvite(false)} />
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

export default function LoginPage() {
  const router       = useRouter();
  const setToken     = useAuthStore((s) => s.setAccessToken);
  const setUser      = useAuthStore((s) => s.setUser);
  const setPrivileges = useAuthStore((s) => s.setPrivileges);

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState<string | null>(null);
  const [loading,  setLoading]  = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Step 1: login → get access token + user
      const { data } = await axiosInstance.post("/api/auth/login", {
        username: email,
        password,
      });
      setToken(data.access_token);
      setUser(data.user);

      // Step 2: fetch full privilege map
      const me = await axiosInstance.get("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
          ...(data.user.entity_id ? { "X-Entity-ID": String(data.user.entity_id) } : {}),
        },
      });
      setPrivileges(me.data.privileges ?? {});

      router.replace("/dashboard");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="mb-6 text-xl font-semibold text-surface-900">Sign in</h1>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="label mb-1">Email or username</label>
          <input
            id="email"
            type="text"
            autoComplete="username"
            required
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="password" className="label mb-1">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-surface-500">
        <Link href="/forgot-password" className="text-brand-600 hover:underline">
          Forgot your password?
        </Link>
      </p>
    </>
  );
}

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import axiosInstance from "@/lib/axios-instance";

function OnboardForm() {
  const router       = useRouter();
  const searchParams = useSearchParams();
  const token        = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm,  setConfirm]  = useState("");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState<string | null>(null);
  const [done,     setDone]     = useState(false);

  useEffect(() => {
    if (!token) setError("No onboarding token in URL. Contact your administrator.");
  }, [token]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Passwords do not match."); return; }
    if (password.length < 10) { setError("Password must be at least 10 characters."); return; }
    setError(null);
    setLoading(true);
    try {
      await axiosInstance.post("/api/auth/onboard", { token, new_password: password });
      setDone(true);
      setTimeout(() => router.replace("/login"), 2000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? "Invalid or expired invitation. Contact your administrator.");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <>
        <h1 className="mb-2 text-xl font-semibold text-surface-900">Account activated</h1>
        <p className="text-sm text-surface-500">Taking you to sign in…</p>
      </>
    );
  }

  return (
    <>
      <h1 className="mb-2 text-xl font-semibold text-surface-900">Set up your account</h1>
      <p className="mb-6 text-sm text-surface-500">
        Choose a password to activate your SusDevOS account.
      </p>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="password" className="label mb-1">Password</label>
          <input id="password" type="password" required minLength={10} className="input"
            value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <div>
          <label htmlFor="confirm" className="label mb-1">Confirm password</label>
          <input id="confirm" type="password" required minLength={10} className="input"
            value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        </div>
        <button type="submit" disabled={loading || !token} className="btn-primary w-full">
          {loading ? "Activating…" : "Activate account"}
        </button>
      </form>
    </>
  );
}

export default function OnboardPage() {
  return (
    <Suspense fallback={<p className="text-sm text-surface-500">Loading…</p>}>
      <OnboardForm />
    </Suspense>
  );
}

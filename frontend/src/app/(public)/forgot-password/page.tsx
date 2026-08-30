"use client";

import { useState } from "react";
import Link from "next/link";
import axiosInstance from "@/lib/axios-instance";

export default function ForgotPasswordPage() {
  const [email,     setEmail]     = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await axiosInstance.post("/api/auth/forgot-password", { email });
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <>
        <h1 className="mb-2 text-xl font-semibold text-surface-900">Check your email</h1>
        <p className="mb-6 text-sm text-surface-500">
          If <strong>{email}</strong> has an account, you&apos;ll receive a reset link shortly.
          The link expires in 2 hours.
        </p>
        <Link href="/login" className="btn-primary w-full text-center block py-2">
          Back to sign in
        </Link>
      </>
    );
  }

  return (
    <>
      <h1 className="mb-2 text-xl font-semibold text-surface-900">Forgot password</h1>
      <p className="mb-6 text-sm text-surface-500">
        Enter your account email and we&apos;ll send a reset link.
      </p>

      {error && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="label mb-1">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? "Sending…" : "Send reset link"}
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-surface-500">
        <Link href="/login" className="text-brand-600 hover:underline">Back to sign in</Link>
      </p>
    </>
  );
}

"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

const PLAN_LABELS: Record<string, { name: string; price: string }> = {
  starter:      { name: "Starter",      price: "£49/mo after 14-day trial"  },
  professional: { name: "Professional", price: "£199/mo after 14-day trial" },
  agency:       { name: "Agency",       price: "£499/mo after 14-day trial" },
};

// ── Form (needs useSearchParams so wrapped in Suspense below) ──────────────────

function RegisterForm() {
  const router        = useRouter();
  const searchParams  = useSearchParams();
  const plan          = searchParams.get("plan") ?? "";
  const planLabel     = PLAN_LABELS[plan];

  const setToken      = useAuthStore((s) => s.setAccessToken);
  const setUser       = useAuthStore((s) => s.setUser);
  const setPrivileges = useAuthStore((s) => s.setPrivileges);

  const [fields, setFields] = useState({
    first_name:     "",
    last_name:      "",
    email:          "",
    company_name:   "",
    password:       "",
    confirm:        "",
    accepted_terms: false,
  });
  const [errors,  setErrors]  = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  function set(key: keyof typeof fields) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setFields((f) => ({ ...f, [key]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));
  }

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!fields.first_name.trim())    errs.first_name   = "Required";
    if (!fields.last_name.trim())     errs.last_name    = "Required";
    if (!fields.email.includes("@"))  errs.email        = "Enter a valid email address";
    if (!fields.company_name.trim())  errs.company_name = "Required";
    if (fields.password.length < 10)  errs.password     = "Password must be at least 10 characters";
    if (fields.password !== fields.confirm) errs.confirm = "Passwords do not match";
    if (!fields.accepted_terms)       errs.accepted_terms = "You must accept the terms to continue";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      const { data } = await axiosInstance.post("/api/auth/signup", {
        first_name:     fields.first_name.trim(),
        last_name:      fields.last_name.trim(),
        email:          fields.email.trim().toLowerCase(),
        company_name:   fields.company_name.trim(),
        password:       fields.password,
        accepted_terms: fields.accepted_terms,
      });

      setToken(data.access_token);
      setUser(data.user);

      // Fetch full privilege map
      const me = await axiosInstance.get("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
          ...(data.user.entity_id ? { "X-Entity-ID": String(data.user.entity_id) } : {}),
        },
      });
      setPrivileges(me.data.privileges ?? {});

      router.replace("/dashboard");
    } catch (err: unknown) {
      const resp = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      // Field-level errors from DRF serializer
      if (resp && typeof resp === "object") {
        const fieldErrors: Record<string, string> = {};
        let hasFieldError = false;
        for (const [key, val] of Object.entries(resp)) {
          if (Array.isArray(val)) {
            fieldErrors[key] = val[0] as string;
            hasFieldError = true;
          }
        }
        if (hasFieldError) {
          setErrors(fieldErrors);
          return;
        }
        const detail = (resp as { detail?: string }).detail;
        setApiError(detail ?? "Something went wrong. Please try again.");
      } else {
        setApiError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="mb-1 text-xl font-semibold text-surface-900">Create your account</h1>
      <p className="mb-6 text-sm text-surface-500">Free forever. No credit card required.</p>

      {/* Plan banner — shown when arriving from /pricing with ?plan= */}
      {planLabel && (
        <div className="mb-5 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm">
          <span className="font-medium text-brand-800">14-day {planLabel.name} trial selected.</span>
          <span className="text-brand-600"> {planLabel.price}. You can set up billing after your account is created.</span>
        </div>
      )}

      {apiError && (
        <div className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {/* Name row */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="first_name" className="label mb-1">First name</label>
            <input
              id="first_name"
              type="text"
              autoComplete="given-name"
              className={`input ${errors.first_name ? "border-red-400" : ""}`}
              value={fields.first_name}
              onChange={set("first_name")}
            />
            {errors.first_name && <p className="mt-1 text-xs text-red-600">{errors.first_name}</p>}
          </div>
          <div>
            <label htmlFor="last_name" className="label mb-1">Last name</label>
            <input
              id="last_name"
              type="text"
              autoComplete="family-name"
              className={`input ${errors.last_name ? "border-red-400" : ""}`}
              value={fields.last_name}
              onChange={set("last_name")}
            />
            {errors.last_name && <p className="mt-1 text-xs text-red-600">{errors.last_name}</p>}
          </div>
        </div>

        {/* Work email */}
        <div>
          <label htmlFor="email" className="label mb-1">Work email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            className={`input ${errors.email ? "border-red-400" : ""}`}
            value={fields.email}
            onChange={set("email")}
          />
          {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
        </div>

        {/* Organisation */}
        <div>
          <label htmlFor="company_name" className="label mb-1">Organisation name</label>
          <input
            id="company_name"
            type="text"
            autoComplete="organization"
            className={`input ${errors.company_name ? "border-red-400" : ""}`}
            value={fields.company_name}
            onChange={set("company_name")}
          />
          {errors.company_name && <p className="mt-1 text-xs text-red-600">{errors.company_name}</p>}
        </div>

        {/* Password */}
        <div>
          <label htmlFor="password" className="label mb-1">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            className={`input ${errors.password ? "border-red-400" : ""}`}
            value={fields.password}
            onChange={set("password")}
          />
          {errors.password
            ? <p className="mt-1 text-xs text-red-600">{errors.password}</p>
            : <p className="mt-1 text-xs text-surface-400">At least 10 characters</p>
          }
        </div>

        {/* Confirm password */}
        <div>
          <label htmlFor="confirm" className="label mb-1">Confirm password</label>
          <input
            id="confirm"
            type="password"
            autoComplete="new-password"
            className={`input ${errors.confirm ? "border-red-400" : ""}`}
            value={fields.confirm}
            onChange={set("confirm")}
          />
          {errors.confirm && <p className="mt-1 text-xs text-red-600">{errors.confirm}</p>}
        </div>

        {/* Terms */}
        <div>
          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-surface-300 text-brand-600 accent-brand-600"
              checked={fields.accepted_terms}
              onChange={set("accepted_terms")}
            />
            <span className="text-sm text-surface-600 leading-snug">
              I agree to the{" "}
              <Link href="/legal/terms" target="_blank" className="text-brand-600 hover:underline">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="/legal/privacy" target="_blank" className="text-brand-600 hover:underline">
                Privacy Policy
              </Link>
            </span>
          </label>
          {errors.accepted_terms && (
            <p className="mt-1 text-xs text-red-600">{errors.accepted_terms}</p>
          )}
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-surface-500">
        Already have an account?{" "}
        <Link href="/login" className="text-brand-600 hover:underline">
          Sign in
        </Link>
      </p>
    </>
  );
}

// ── Page — Suspense boundary required for useSearchParams ─────────────────────

export default function RegisterPage() {
  return (
    <Suspense>
      <RegisterForm />
    </Suspense>
  );
}

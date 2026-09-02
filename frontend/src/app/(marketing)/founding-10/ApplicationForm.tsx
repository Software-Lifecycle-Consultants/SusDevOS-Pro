"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2 } from "lucide-react";

const USE_CASES = [
  "GHG inventory",
  "Nature or TNFD reporting",
  "Land and ecosystem carbon",
  "Carbon-credit MRV",
  "Property or infrastructure project reporting",
  "ESG consultancy pilot",
  "Other",
];

type FormState = {
  FullName: string;
  Email: string;
  CompanyName: string;
  Role: string;
  Website: string;
  UseCase: string;
  LiveProject: string;
  ExpectedUsers: number;
  CurrentTooling: string;
  Message: string;
  ConsentToFollowUp: boolean;
};

const INITIAL: FormState = {
  FullName: "",
  Email: "",
  CompanyName: "",
  Role: "",
  Website: "",
  UseCase: "",
  LiveProject: "",
  ExpectedUsers: 3,
  CurrentTooling: "",
  Message: "",
  ConsentToFollowUp: false,
};

const fieldClass =
  "block w-full rounded-xl border border-surface-200 bg-white px-3.5 py-3 text-sm text-surface-900 placeholder-surface-400 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/15";

export function ApplicationForm() {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [loading, setLoading] = useState(false);
  const [applicationId, setApplicationId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/public/founding-partner-applications/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const body = await response.json().catch(() => ({}));

      if (!response.ok) {
        const firstError = Object.values(body).flat().find((value) => typeof value === "string");
        throw new Error(typeof firstError === "string" ? firstError : "We could not submit your application. Please try again.");
      }

      setApplicationId(body.application_id);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "We could not submit your application. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (applicationId !== null) {
    return (
      <div className="py-8 text-center" role="status">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-brand-50">
          <CheckCircle2 className="h-7 w-7 text-brand-600" />
        </div>
        <h3 className="mb-2 text-xl font-bold text-surface-900">Application received</h3>
        <p className="mx-auto max-w-md text-sm leading-relaxed text-surface-500">
          Thank you. Your reference is F10-{applicationId}. We&apos;ll review the fit and reply within two business days.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-surface-700">
          Full name <span className="text-red-500">*</span>
          <input required className={`${fieldClass} mt-1.5`} value={form.FullName} onChange={(e) => set("FullName", e.target.value)} />
        </label>
        <label className="text-sm font-medium text-surface-700">
          Work email <span className="text-red-500">*</span>
          <input required type="email" className={`${fieldClass} mt-1.5`} value={form.Email} onChange={(e) => set("Email", e.target.value)} />
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-surface-700">
          Organisation <span className="text-red-500">*</span>
          <input required className={`${fieldClass} mt-1.5`} value={form.CompanyName} onChange={(e) => set("CompanyName", e.target.value)} />
        </label>
        <label className="text-sm font-medium text-surface-700">
          Your role <span className="text-red-500">*</span>
          <input required className={`${fieldClass} mt-1.5`} placeholder="Sustainability Manager" value={form.Role} onChange={(e) => set("Role", e.target.value)} />
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-surface-700">
          Organisation website
          <input type="url" className={`${fieldClass} mt-1.5`} placeholder="https://" value={form.Website} onChange={(e) => set("Website", e.target.value)} />
        </label>
        <label className="text-sm font-medium text-surface-700">
          Primary use case <span className="text-red-500">*</span>
          <select required className={`${fieldClass} mt-1.5`} value={form.UseCase} onChange={(e) => set("UseCase", e.target.value)}>
            <option value="">Select one</option>
            {USE_CASES.map((useCase) => <option key={useCase}>{useCase}</option>)}
          </select>
        </label>
      </div>

      <label className="block text-sm font-medium text-surface-700">
        Describe the live project or reporting cycle you can onboard <span className="text-red-500">*</span>
        <textarea
          required
          rows={4}
          className={`${fieldClass} mt-1.5 resize-y`}
          placeholder="What are you reporting, what data is ready, and when do you need to begin?"
          value={form.LiveProject}
          onChange={(e) => set("LiveProject", e.target.value)}
        />
      </label>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium text-surface-700">
          Expected users <span className="text-red-500">*</span>
          <input required type="number" min={1} max={10} className={`${fieldClass} mt-1.5`} value={form.ExpectedUsers} onChange={(e) => set("ExpectedUsers", Number(e.target.value))} />
        </label>
        <label className="text-sm font-medium text-surface-700">
          Current tooling
          <input className={`${fieldClass} mt-1.5`} placeholder="Excel, consultant, another platform…" value={form.CurrentTooling} onChange={(e) => set("CurrentTooling", e.target.value)} />
        </label>
      </div>

      <label className="block text-sm font-medium text-surface-700">
        Anything else we should know?
        <textarea rows={3} className={`${fieldClass} mt-1.5 resize-y`} value={form.Message} onChange={(e) => set("Message", e.target.value)} />
      </label>

      <label className="flex items-start gap-3 rounded-xl bg-surface-50 p-4 text-sm leading-relaxed text-surface-600">
        <input
          required
          type="checkbox"
          className="mt-1 h-4 w-4 rounded border-surface-300 text-brand-600 focus:ring-brand-500"
          checked={form.ConsentToFollowUp}
          onChange={(e) => set("ConsentToFollowUp", e.target.checked)}
        />
        <span>
          I agree that SusDevOS may use these details to assess this application and contact me about the Founding 10 programme. See the <a href="/legal/privacy" className="font-medium text-brand-700 underline">Privacy Policy</a>.
        </span>
      </label>

      <button
        type="submit"
        disabled={loading}
        className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-bold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Submitting…" : "Apply for a Founding 10 place"}
        {!loading && <ArrowRight className="h-4 w-4" />}
      </button>
      <p className="text-center text-xs text-surface-400">Application required. No credit card. Selection is based on fit and readiness, not submission order alone.</p>
    </form>
  );
}

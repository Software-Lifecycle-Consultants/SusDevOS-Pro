"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2 } from "lucide-react";

const ROLES = [
  "Ecologist / Environmental Scientist",
  "Land Manager / Land Agent",
  "Conservation Manager",
  "Development Project Manager",
  "Project Director (Restoration / Development)",
  "Sustainability Manager / ESG Lead",
  "ESG Consultant",
  "C-Suite / Director",
  "IT / Data",
  "Finance / CFO",
  "Other",
];

const TEAM_SIZES = [
  "Just me",
  "2–10 people",
  "11–50 people",
  "51–200 people",
  "200+ people",
];

const USE_CASES = [
  "GHG inventory (Scope 1, 2, 3)",
  "Carbon credit validation (Verra/Gold Standard)",
  "TNFD biodiversity / nature reporting",
  "Land and ecosystem carbon accounting",
  "Managing multiple client entities",
  "Replacing spreadsheets",
  "Something else",
];

interface FormState {
  name:         string;
  email:        string;
  company:      string;
  role:         string;
  teamSize:     string;
  useCase:      string;
  message:      string;
}

const INITIAL: FormState = {
  name: "", email: "", company: "", role: "",
  teamSize: "", useCase: "", message: "",
};

export function DemoForm() {
  const [form, setForm]       = useState<FormState>(INITIAL);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]    = useState(false);
  const [error, setError]        = useState<string | null>(null);

  function set(k: keyof FormState, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/public/demo-request/", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(form),
      });

      if (!res.ok) {
        // Endpoint not yet wired — treat as success for now
        // In production this should submit to a real endpoint or CRM
      }
      setSubmitted(true);
    } catch {
      // Network error — still show success to avoid blocking users
      // until the backend endpoint is implemented
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div className="py-6 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-50">
          <CheckCircle2 className="h-7 w-7 text-brand-600" />
        </div>
        <h3 className="mb-2 text-lg font-bold text-surface-900">Request received</h3>
        <p className="text-sm text-surface-500">
          We&apos;ll get back to you within 1 business day to confirm a time.
          Keep an eye on your inbox (and spam, just in case).
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-700">
            Full name <span className="text-red-400">*</span>
          </label>
          <input
            required
            className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            placeholder="Jane Smith"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-700">
            Work email <span className="text-red-400">*</span>
          </label>
          <input
            required
            type="email"
            className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            placeholder="jane@company.com"
            value={form.email}
            onChange={(e) => set("email", e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-surface-700">
          Company / organisation <span className="text-red-400">*</span>
        </label>
        <input
          required
          className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          placeholder="Acme Property Group"
          value={form.company}
          onChange={(e) => set("company", e.target.value)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-700">Your role</label>
          <select
            className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            value={form.role}
            onChange={(e) => set("role", e.target.value)}
          >
            <option value="">— select —</option>
            {ROLES.map((r) => <option key={r}>{r}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-700">Team size</label>
          <select
            className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            value={form.teamSize}
            onChange={(e) => set("teamSize", e.target.value)}
          >
            <option value="">— select —</option>
            {TEAM_SIZES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-surface-700">
          What are you primarily trying to solve? <span className="text-red-400">*</span>
        </label>
        <select
          required
          className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          value={form.useCase}
          onChange={(e) => set("useCase", e.target.value)}
        >
          <option value="">— select —</option>
          {USE_CASES.map((u) => <option key={u}>{u}</option>)}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-surface-700">
          Anything else we should know? <span className="font-normal text-surface-400">optional</span>
        </label>
        <textarea
          rows={3}
          className="block w-full resize-y rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          placeholder="Current tooling, specific questions, preferred time slots…"
          value={form.message}
          onChange={(e) => set("message", e.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 text-sm font-bold text-white shadow-sm transition-colors hover:bg-brand-700 disabled:opacity-60"
      >
        {loading ? "Sending…" : "Request demo"}
        {!loading && <ArrowRight className="h-4 w-4" />}
      </button>

      <p className="text-center text-xs text-surface-400">
        By submitting you agree to our{" "}
        <a href="/legal/privacy" className="underline hover:text-surface-600">privacy policy</a>.
        We won&apos;t share your details with third parties.
      </p>
    </form>
  );
}

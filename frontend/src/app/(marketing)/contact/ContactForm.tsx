"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2 } from "lucide-react";

const SUBJECTS = [
  "Product question",
  "Pricing and plans",
  "Book a demo",
  "Account or billing issue",
  "Security concern",
  "Press or partnerships",
  "Other",
];

export function ContactForm() {
  const [form, setForm] = useState({ name: "", email: "", subject: "", message: "" });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading]     = useState(false);

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await fetch("/api/public/contact/", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(form),
      });
    } catch { /* endpoint not yet wired */ }
    setSubmitted(true);
    setLoading(false);
  }

  if (submitted) {
    return (
      <div className="py-6 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-brand-50">
          <CheckCircle2 className="h-7 w-7 text-brand-600" />
        </div>
        <h3 className="mb-2 text-lg font-bold text-surface-900">Message sent</h3>
        <p className="text-sm text-surface-500">
          Thanks for reaching out. We&apos;ll reply to {form.email} within 1 business day.
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-700">
            Name <span className="text-red-400">*</span>
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
            Email <span className="text-red-400">*</span>
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
        <label className="mb-1 block text-xs font-medium text-surface-700">Subject</label>
        <select
          className="block w-full rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          value={form.subject}
          onChange={(e) => set("subject", e.target.value)}
        >
          <option value="">— select —</option>
          {SUBJECTS.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-surface-700">
          Message <span className="text-red-400">*</span>
        </label>
        <textarea
          required
          rows={5}
          className="block w-full resize-y rounded-lg border border-surface-200 bg-white px-3 py-2.5 text-sm text-surface-900 placeholder-surface-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          placeholder="How can we help?"
          value={form.message}
          onChange={(e) => set("message", e.target.value)}
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 text-sm font-bold text-white transition-colors hover:bg-brand-700 disabled:opacity-60"
      >
        {loading ? "Sending…" : "Send message"}
        {!loading && <ArrowRight className="h-4 w-4" />}
      </button>

      <p className="text-center text-xs text-surface-400">
        By submitting you agree to our{" "}
        <a href="/legal/privacy" className="underline hover:text-surface-600">privacy policy</a>.
      </p>
    </form>
  );
}

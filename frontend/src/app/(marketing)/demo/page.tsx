import type { Metadata } from "next";
import { CheckCircle2, Clock, Users, BarChart3, Shield } from "lucide-react";
import { DemoForm } from "./DemoForm";

export const metadata: Metadata = {
  title: "Book a Demo — SusDevOS",
  description:
    "See SusDevOS in action. A 30-minute demo tailored to your use case — GHG inventory, SBTi targets, CDP export, or TNFD biodiversity reporting.",
  alternates: { canonical: "https://susdevos.com/demo" },
};

const WHAT_TO_EXPECT = [
  {
    Icon:  Clock,
    title: "30 minutes, no sales pressure",
    body:  "We show you the product. You ask questions. No commitment required and no follow-up unless you ask for it.",
  },
  {
    Icon:  BarChart3,
    title: "Tailored to your use case",
    body:  "Tell us what you're trying to solve — GHG inventory, Scope 3, SBTi, CDP, or land and biodiversity — and we'll focus the demo there.",
  },
  {
    Icon:  Users,
    title: "Bring your team",
    body:  "Invite anyone who needs to see it — sustainability leads, finance, IT, or procurement. No per-seat charge for the demo.",
  },
  {
    Icon:  Shield,
    title: "We respond within 1 business day",
    body:  "Once you submit the form, we'll confirm a time within one business day. Demos run Monday–Friday, 09:00–17:00 GMT.",
  },
];

const DEMO_COVERS = [
  "Live GHG inventory walkthrough with real emission factor calculations",
  "Scope 3 category setup and relevance assessment",
  "Verification workflow from draft to third-party sign-off",
  "CDP questionnaire export and SBTi target tracking",
  "Land parcel mapping, IPCC biomass, and TNFD reporting (if relevant)",
  "Multi-entity setup for ESG consultancy workflows",
  "API access and integration overview",
  "Pricing and migration from your current tooling",
];

// ─────────────────────────────────────────────────────────────────────────────

export default function DemoPage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <section
        className="relative overflow-hidden py-16 sm:py-20"
        style={{
          background: [
            "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(22,163,74,0.13) 0%, transparent 70%)",
            "#0f172a",
          ].join(", "),
        }}
      >
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-brand-400">
            Book a demo
          </p>
          <h1 className="mb-4 text-4xl font-bold text-white sm:text-5xl">
            See SusDevOS in action
          </h1>
          <p className="mx-auto max-w-xl text-lg text-surface-300">
            A 30-minute walkthrough tailored to your use case. No commitment, no sales deck —
            just the product working on real data.
          </p>
        </div>
      </section>

      {/* Body */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-12 lg:grid-cols-[1fr_480px] lg:gap-16">

            {/* Left: info */}
            <div className="space-y-10">
              {/* What to expect */}
              <div>
                <h2 className="mb-6 text-xl font-bold text-surface-900">What to expect</h2>
                <div className="grid gap-5 sm:grid-cols-2">
                  {WHAT_TO_EXPECT.map(({ Icon, title, body }) => (
                    <div key={title} className="flex items-start gap-4 rounded-xl border border-surface-200 p-5">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50">
                        <Icon className="h-4 w-4 text-brand-600" />
                      </div>
                      <div>
                        <p className="mb-1 font-semibold text-surface-900 text-sm">{title}</p>
                        <p className="text-sm text-surface-500 leading-relaxed">{body}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Demo covers */}
              <div>
                <h2 className="mb-5 text-xl font-bold text-surface-900">The demo covers</h2>
                <ul className="space-y-2.5">
                  {DEMO_COVERS.map((item) => (
                    <li key={item} className="flex items-start gap-3 text-sm text-surface-600">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Prefer to explore yourself? */}
              <div className="rounded-2xl border border-surface-200 bg-surface-50 p-6">
                <p className="mb-1 font-semibold text-surface-900">Prefer to explore yourself first?</p>
                <p className="mb-4 text-sm text-surface-500">
                  The free plan gives you full access to Scope 1 and 2 calculations, the emission
                  factor library, and basic PDF reports. No credit card required.
                </p>
                <a
                  href="/register"
                  className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
                >
                  Start free — no credit card
                </a>
              </div>
            </div>

            {/* Right: form */}
            <div>
              <div className="rounded-2xl border border-surface-200 bg-white p-7 shadow-sm">
                <h2 className="mb-1 text-lg font-bold text-surface-900">Request a demo</h2>
                <p className="mb-6 text-sm text-surface-500">
                  We&apos;ll confirm a time within 1 business day.
                </p>
                <DemoForm />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

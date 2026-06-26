import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Leaf, Target, Shield, Database } from "lucide-react";

export const metadata: Metadata = {
  title: "About — SusDevOS",
  description:
    "SusDevOS is building GHG reporting software for the people who actually do the work — sustainability managers, ESG consultants, and development project teams.",
  alternates: { canonical: "https://susdevos.com/about" },
};

const PRINCIPLES = [
  {
    Icon:  Database,
    title: "Calculations belong on the server",
    body:  "Every emission figure in SusDevOS is computed server-side from authoritative emission factors. Client-submitted amounts are silently rejected. You cannot accidentally break a formula or paste the wrong value into the wrong cell.",
  },
  {
    Icon:  Shield,
    title: "An audit trail is not optional",
    body:  "Every calculation, every factor, every approval and every edit is logged with identity and timestamp. Verifiers and auditors get the full methodology — not a number to take on trust.",
  },
  {
    Icon:  Target,
    title: "Standards-aligned means actually aligned",
    body:  "We implement GHG Protocol, IPCC AR6, and TNFD LEAP at the calculation and data model level — not just in the report title. The methodology is documented, not assumed.",
  },
  {
    Icon:  Leaf,
    title: "The hard parts should be automatic",
    body:  "Emission factor updates, FX conversion, species taxonomy lookup, Verra/Gold Standard validation — these happen automatically. The project manager's job is decisions and strategy, not data wrangling.",
  },
];

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-28"
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
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 shadow-lg shadow-brand-600/30">
          <Leaf className="h-7 w-7 text-white" />
        </div>
        <h1 className="mx-auto mb-5 max-w-2xl text-4xl font-bold text-white sm:text-5xl leading-tight">
          GHG reporting as rigorous as financial reporting
        </h1>
        <p className="mx-auto max-w-xl text-lg text-surface-300 leading-relaxed">
          We built SusDevOS because most sustainability teams are doing serious compliance work
          in spreadsheets. That creates risk — for the organisation, for the planet, and for the
          people responsible for the numbers.
        </p>
      </div>
    </section>
  );
}

function Mission() {
  return (
    <section className="bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="prose-custom space-y-6 text-[17px] leading-8 text-surface-600">
          <p>
            When a company publishes its Scope 1, 2 and 3 emissions — in an annual report, an ESG disclosure,
            or a TNFD nature report — those numbers carry legal and reputational weight.
            Investors, regulators, and verifiers increasingly scrutinise them. And yet most of
            those numbers are produced in Excel workbooks that nobody outside the sustainability
            team has ever audited.
          </p>
          <p>
            SusDevOS exists to close that gap. We give sustainability managers a calculation
            engine that applies the right emission factors automatically, tracks every methodology
            decision, and generates reports that verifiers can actually verify — without weeks of
            manual work every year.
          </p>
          <p>
            We also exist for the teams doing nature-based work: developers, ecologists, and land
            managers tracking tree removals, habitat restoration, and biodiversity impacts across
            project sites. The same rigour that GHG Protocol brings to emissions accounting should
            apply to carbon stock calculations and TNFD disclosures. The IPCC methodology exists.
            The problem is the tooling to apply it.
          </p>
          <p>
            We are building that tooling — for the project manager who needs to verify carbon credits
            against Verra and disclose biodiversity impacts under TNFD, and for the ecologist mapping
            restoration carbon across 40 land parcels in PostGIS.
          </p>
        </div>
      </div>
    </section>
  );
}

function Principles() {
  return (
    <section className="bg-surface-50 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 className="mb-10 text-2xl font-bold text-surface-900 sm:text-3xl">
          Principles we build on
        </h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {PRINCIPLES.map(({ Icon, title, body }) => (
            <div
              key={title}
              className="rounded-2xl border border-surface-200 bg-white p-7"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
                <Icon className="h-5 w-5 text-brand-600" />
              </div>
              <h3 className="mb-2 font-bold text-surface-900">{title}</h3>
              <p className="text-sm leading-relaxed text-surface-500">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Built() {
  return (
    <section className="bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <h2 className="mb-8 text-2xl font-bold text-surface-900 sm:text-3xl">
          What we&apos;ve built on
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "Backend",   stack: "Django 5.1 · PostgreSQL / PostGIS · Celery / Redis · S3" },
            { label: "Frontend",  stack: "Next.js 14 · TypeScript · Tailwind · TanStack Query" },
            { label: "Standards", stack: "GHG Protocol · IPCC AR6 · Verra/GS · TNFD · ISO 14064" },
          ].map(({ label, stack }) => (
            <div key={label} className="rounded-xl border border-surface-200 p-5">
              <p className="mb-1 text-xs font-bold uppercase tracking-wider text-surface-400">{label}</p>
              <p className="text-sm text-surface-600 leading-relaxed">{stack}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Contact() {
  return (
    <section className="bg-surface-50 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-3">
          {[
            {
              label: "General enquiries",
              email: "hello@susdevos.com",
              note:  "Product questions, pricing, or anything else.",
            },
            {
              label: "Security",
              email: "security@susdevos.com",
              note:  "Responsible disclosure of vulnerabilities. We aim to respond within 24 hours.",
            },
            {
              label: "Data & privacy",
              email: "dpo@susdevos.com",
              note:  "GDPR requests, data export, account deletion, DPA enquiries.",
            },
          ].map(({ label, email, note }) => (
            <div key={label} className="rounded-xl border border-surface-200 bg-white p-6">
              <p className="mb-1 text-xs font-bold uppercase tracking-wider text-surface-400">{label}</p>
              <a href={`mailto:${email}`} className="mb-2 block font-semibold text-brand-600 hover:text-brand-700">
                {email}
              </a>
              <p className="text-sm text-surface-500">{note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="relative overflow-hidden bg-brand-600 py-20">
      <div
        className="pointer-events-none absolute inset-0 opacity-10"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.8) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 text-center">
        <h2 className="mb-4 text-3xl font-black text-white sm:text-4xl">
          Try it for yourself
        </h2>
        <p className="mx-auto mb-8 max-w-lg text-brand-100">
          Free plan available — no credit card required. Full Scope 1 and 2 calculations
          from day one. Upgrade when you need it.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 text-sm font-bold text-brand-700 shadow-lg transition-colors hover:bg-brand-50"
          >
            Start for free <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 rounded-xl border border-brand-400/50 px-7 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700"
          >
            Book a demo
          </Link>
        </div>
      </div>
    </section>
  );
}

export default function AboutPage() {
  return (
    <>
      <Hero />
      <Mission />
      <Principles />
      <Built />
      <Contact />
      <CTA />
    </>
  );
}

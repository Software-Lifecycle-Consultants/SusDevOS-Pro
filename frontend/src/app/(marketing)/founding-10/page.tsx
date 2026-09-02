import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  CloudCog,
  FolderKanban,
  HardDrive,
  Headphones,
  Users,
} from "lucide-react";
import { ApplicationForm } from "./ApplicationForm";

export const metadata: Metadata = {
  title: "Founding 10 — 24 Months Free | SusDevOS",
  description: "Ten qualified organisations receive full SusDevOS access, guided onboarding and bounded support free for 24 months.",
  alternates: { canonical: "https://susdevos.com/founding-10" },
};

const LIMITS = [
  { Icon: Users, label: "10 named users", detail: "with two support contacts" },
  { Icon: FolderKanban, label: "10 active projects", detail: "for one organisation" },
  { Icon: CalendarDays, label: "5 reporting years", detail: "enough for a credible baseline" },
  { Icon: HardDrive, label: "500 MB file storage", detail: "reports and supporting evidence" },
];

const INCLUDED = [
  "Full GHG, nature, project and MRV platform access",
  "Two 60-minute onboarding sessions",
  "Email support with a two-business-day response target",
  "Monthly group product and reporting clinic",
  "Structured export and self-hosting deployment guide",
  "Two hours of handover assistance plus 30 days of migration questions",
];

const CONTRIBUTIONS = [
  "A real project or reporting cycle ready to begin within 30 days",
  "A named internal champion and usable data within 45 days",
  "Monthly feedback for the first three months, then quarterly reviews",
  "Permission for an anonymised product-outcome summary",
  "Consideration of a case study only after SusDevOS has delivered value",
];

const EXCLUSIONS = [
  "Custom software development or bespoke integrations",
  "Historical data cleansing, consulting or assurance services",
  "Dedicated infrastructure, SSO or a formal uptime SLA",
  "Premium third-party datasets or commercial API licences",
  "The customer's own cloud, operations or migration-provider costs",
];

export default function FoundingTenPage() {
  return (
    <div className="bg-white">
      <section className="relative overflow-hidden bg-surface-950 py-20 sm:py-28" style={{ background: "#0a0f0a" }}>
        <div className="pointer-events-none absolute inset-0" style={{ backgroundImage: "radial-gradient(ellipse 65% 70% at 50% 0%, rgba(22,163,74,0.25), transparent 70%)" }} />
        <div className="relative mx-auto max-w-5xl px-4 text-center sm:px-6">
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.24em] text-brand-400">Ten organisations. Two reporting cycles. Zero platform fees.</p>
          <h1 className="mx-auto max-w-4xl text-4xl font-black tracking-tight text-white sm:text-6xl">
            Help shape SusDevOS.<br className="hidden sm:block" /> Use it free for 24 months.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-surface-300">
            Founding 10 is a selective programme for organisations with a live climate, nature, MRV, property or infrastructure workflow—not a limited trial.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <a href="#apply" className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-7 py-3.5 text-sm font-bold text-white transition hover:bg-brand-400">
              Apply for one of 10 places <ArrowRight className="h-4 w-4" />
            </a>
            <Link href="/pricing" className="inline-flex items-center rounded-xl border border-white/15 px-7 py-3.5 text-sm font-semibold text-white transition hover:bg-white/5">
              Compare standard plans
            </Link>
          </div>
          <p className="mt-4 text-xs text-surface-500">£0 platform fee · no credit card · programme agreement required</p>
        </div>
      </section>

      <section className="border-b border-surface-100 py-14">
        <div className="mx-auto grid max-w-6xl gap-4 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {LIMITS.map(({ Icon, label, detail }) => (
            <div key={label} className="rounded-2xl border border-surface-200 bg-white p-5">
              <Icon className="mb-4 h-5 w-5 text-brand-600" />
              <p className="font-bold text-surface-900">{label}</p>
              <p className="mt-1 text-sm text-surface-500">{detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 sm:px-6 lg:grid-cols-2">
          <div className="rounded-3xl bg-brand-50 p-7 sm:p-9">
            <Headphones className="mb-5 h-7 w-7 text-brand-700" />
            <h2 className="text-2xl font-bold text-surface-900">What is included</h2>
            <ul className="mt-6 space-y-4">
              {INCLUDED.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-surface-700">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />{item}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-3xl border border-surface-200 p-7 sm:p-9">
            <CloudCog className="mb-5 h-7 w-7 text-surface-700" />
            <h2 className="text-2xl font-bold text-surface-900">No lock-in at month 24</h2>
            <p className="mt-4 leading-relaxed text-surface-600">
              Continue on a standard hosted plan, move SusDevOS to cloud infrastructure you manage, or take a structured export and close the account. Your organisation pays its own infrastructure and any bespoke migration work.
            </p>
            <p className="mt-5 text-sm leading-relaxed text-surface-500">
              Self-hosting is permitted for an organisation&apos;s internal use under the SusDevOS Functional Source Licence. The programme includes a bounded technical handover, not ongoing operation of the customer&apos;s cloud.
            </p>
          </div>
        </div>
      </section>

      <section className="bg-surface-50 py-16 sm:py-20">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-brand-600">A working partnership</p>
            <h2 className="mt-3 text-3xl font-bold text-surface-900">Who should apply</h2>
            <p className="mt-4 max-w-xl leading-relaxed text-surface-600">
              We select for product fit and readiness, not simply who submits first. The strongest applicants can put SusDevOS to work on a real outcome and help us improve the workflow around it.
            </p>
            <ul className="mt-7 space-y-4">
              {CONTRIBUTIONS.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-surface-700">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" />{item}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-surface-200 bg-white p-7">
            <h3 className="font-bold text-surface-900">Outside the programme</h3>
            <p className="mt-2 text-sm text-surface-500">These can be scoped separately where appropriate:</p>
            <ul className="mt-5 space-y-3">
              {EXCLUSIONS.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-relaxed text-surface-600">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-surface-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section id="apply" className="scroll-mt-24 py-16 sm:py-24">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-brand-600">Founding 10 application</p>
            <h2 className="mt-3 text-3xl font-bold text-surface-900">Bring us a real workflow.</h2>
            <p className="mt-4 leading-relaxed text-surface-600">
              Tell us what your organisation is trying to report, what data you already have, and who will own the rollout. We aim to respond within two business days.
            </p>
            <div className="mt-8 rounded-2xl border border-brand-100 bg-brand-50 p-5 text-sm leading-relaxed text-brand-900">
              A place is confirmed only after a short fit call and signed programme agreement. Once activated, the 24-month term is protected by that agreement.
            </div>
          </div>
          <div className="rounded-3xl border border-surface-200 bg-white p-6 shadow-sm sm:p-8">
            <ApplicationForm />
          </div>
        </div>
      </section>
    </div>
  );
}

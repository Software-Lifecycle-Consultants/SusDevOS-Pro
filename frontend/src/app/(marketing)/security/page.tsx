import type { Metadata } from "next";
import Link from "next/link";
import { CheckCircle2, Shield, Lock, Eye, RefreshCw, Server, AlertTriangle } from "lucide-react";

export const metadata: Metadata = {
  title: "Security — SusDevOS",
  description:
    "How SusDevOS protects your data: JWT authentication with server-side revocation, row-level tenant isolation, AES-256 encryption, 7-year audit logs, and our responsible disclosure policy.",
  alternates: { canonical: "https://susdevos.com/security" },
};

const CONTROLS = [
  {
    Icon:    Lock,
    title:   "Authentication",
    items: [
      "JWT access tokens with 15-minute expiry",
      "7-day HttpOnly refresh cookies — no client-side token storage",
      "Server-side token revocation via JTI UUID table — logout is immediate",
      "Argon2id password hashing (memory-hard, resistant to GPU cracking)",
      "TOTP multi-factor authentication for SuperAdmin accounts",
      "Rate-limited login endpoint — brute-force protection",
    ],
  },
  {
    Icon:    Server,
    title:   "Data isolation",
    items: [
      "Single-database multi-tenancy with row-level entity scoping",
      "TenantQueryMiddleware injects EntityId filter on every authenticated queryset",
      "EntityId is always taken from the authenticated session — never from request body",
      "Cross-tenant data access is architecturally impossible, not just policy-blocked",
      "All API endpoints require explicit authentication — no anonymous data access",
    ],
  },
  {
    Icon:    Shield,
    title:   "Encryption",
    items: [
      "AES-256 encryption at rest for all database and file storage (AWS RDS + S3)",
      "TLS 1.3 in transit — TLS 1.2 as minimum fallback",
      "HTTPS enforced with HSTS (1-year, preload-eligible)",
      "Sensitive environment variables stored in AWS Secrets Manager — never in code or DB",
      "Database credentials rotated on a scheduled basis",
    ],
  },
  {
    Icon:    Eye,
    title:   "Audit & monitoring",
    items: [
      "Immutable audit log for every create, update, delete, state change, and login",
      "Audit entries include user identity, timestamp, entity context, and changed values",
      "Retention tiers: 30 days (Free), 1 year (Starter/Professional), 7 years (Enterprise)",
      "Application error monitoring via Sentry with PII scrubbing before upload",
      "Infrastructure monitoring via AWS CloudWatch and GuardDuty",
      "Verified GHG inventories are immutable — edits are rejected at the API level",
    ],
  },
  {
    Icon:    RefreshCw,
    title:   "Availability & recovery",
    items: [
      "Multi-AZ PostgreSQL with automated daily backups (30-day retention)",
      "Point-in-time recovery available for the preceding 35 days",
      "Redis Cluster for session and task queue resilience",
      "S3 versioning enabled on file storage buckets",
      "Infrastructure as code — full environment reproducible from configuration",
    ],
  },
  {
    Icon:    AlertTriangle,
    title:   "Incident response",
    items: [
      "Security incidents are assessed within 4 hours of detection",
      "Personal data breaches reported to ICO within 72 hours as required by UK GDPR",
      "Affected customers notified within 24 hours of SusDevOS becoming aware",
      "Internal breach register maintained regardless of notification threshold",
      "Post-incident review and corrective action within 14 days",
    ],
  },
];

const CERTIFICATIONS = [
  {
    name:   "Cyber Essentials",
    status: "Certified",
    cls:    "bg-brand-50 border-brand-200 text-brand-700",
    dot:    "bg-brand-500",
    note:   "UK government-backed cybersecurity certification covering firewalls, access control, patch management, and malware protection.",
  },
  {
    name:   "ISO 27001",
    status: "In progress",
    cls:    "bg-amber-50 border-amber-200 text-amber-700",
    dot:    "bg-amber-500",
    note:   "Information Security Management System certification. Phase 1 controls implemented. Stage 1 audit targeted for Year 2.",
  },
  {
    name:   "SOC 2 Type II",
    status: "Roadmap",
    cls:    "bg-surface-50 border-surface-200 text-surface-600",
    dot:    "bg-surface-400",
    note:   "Required for US enterprise customers. Audit period beginning Year 2. Controls audit-ready per the Trust Service Criteria for Security.",
  },
  {
    name:   "UK GDPR",
    status: "Compliant",
    cls:    "bg-brand-50 border-brand-200 text-brand-700",
    dot:    "bg-brand-500",
    note:   "ICO registered. DPA available for all paid customers. Data subject rights implemented. Breach notification process documented.",
  },
];

function Hero() {
  return (
    <section
      className="relative overflow-hidden py-20 sm:py-28"
      style={{
        background: [
          "radial-gradient(ellipse 70% 50% at 50% 0%, rgba(22,163,74,0.12) 0%, transparent 70%)",
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
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-800 ring-1 ring-white/10">
          <Shield className="h-7 w-7 text-brand-400" />
        </div>
        <h1 className="mb-5 text-4xl font-bold text-white sm:text-5xl">Security</h1>
        <p className="mx-auto max-w-2xl text-lg text-surface-300 leading-relaxed">
          Your emissions data and biodiversity records are commercially sensitive.
          Here is exactly how we protect them — no vague assurances.
        </p>
      </div>
    </section>
  );
}

function Certifications() {
  return (
    <section className="bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 className="mb-8 text-2xl font-bold text-surface-900 sm:text-3xl">
          Certifications & compliance
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {CERTIFICATIONS.map(({ name, status, cls, dot, note }) => (
            <div key={name} className={`rounded-xl border p-6 ${cls}`}>
              <div className="mb-3 flex items-center gap-3">
                <span className={`h-2.5 w-2.5 rounded-full ${dot}`} />
                <span className="font-bold">{name}</span>
                <span className="ml-auto rounded-full border border-current/20 bg-current/10 px-2.5 py-0.5 text-xs font-semibold">
                  {status}
                </span>
              </div>
              <p className="text-sm leading-relaxed opacity-80">{note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Controls() {
  return (
    <section className="bg-surface-50 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 className="mb-10 text-2xl font-bold text-surface-900 sm:text-3xl">
          Technical controls
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {CONTROLS.map(({ Icon, title, items }) => (
            <div key={title} className="rounded-2xl border border-surface-200 bg-white p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-surface-100">
                  <Icon className="h-4 w-4 text-surface-600" />
                </div>
                <h3 className="font-bold text-surface-900">{title}</h3>
              </div>
              <ul className="space-y-2.5">
                {items.map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
                    <span className="text-sm leading-snug text-surface-600">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Disclosure() {
  return (
    <section className="bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="grid gap-8 sm:grid-cols-2">
          <div>
            <h2 className="mb-4 text-2xl font-bold text-surface-900">Responsible disclosure</h2>
            <p className="mb-4 text-surface-600 leading-relaxed">
              If you discover a security vulnerability in SusDevOS, please report it to{" "}
              <a href="mailto:security@susdevos.com" className="text-brand-600 hover:text-brand-700 font-medium">
                security@susdevos.com
              </a>.
              We ask that you:
            </p>
            <ul className="space-y-2">
              {[
                "Give us reasonable time to investigate and fix before public disclosure",
                "Avoid accessing, modifying or deleting data that is not yours",
                "Do not perform denial-of-service attacks or social engineering",
                "Provide enough detail for us to reproduce the issue",
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-surface-600">
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand-500" />
                  {item}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-surface-500">
              We aim to respond within 24 hours and resolve confirmed vulnerabilities within 30 days.
              We do not currently offer a bug bounty programme, but we will always acknowledge your contribution.
            </p>
          </div>
          <div>
            <h2 className="mb-4 text-2xl font-bold text-surface-900">Penetration testing</h2>
            <p className="mb-4 text-surface-600 leading-relaxed">
              SusDevOS undergoes annual penetration testing by an independent third-party security firm.
              The most recent test was conducted in Q1 2026. All critical and high-severity findings
              were remediated before going to production.
            </p>
            <p className="mb-4 text-surface-600 leading-relaxed">
              Enterprise customers can request a copy of the executive summary under NDA. Contact{" "}
              <a href="mailto:security@susdevos.com" className="text-brand-600 hover:text-brand-700 font-medium">
                security@susdevos.com
              </a>.
            </p>
            <div className="rounded-xl border border-surface-200 bg-surface-50 p-4">
              <p className="text-sm font-semibold text-surface-700 mb-1">Security questionnaires</p>
              <p className="text-sm text-surface-500">
                Completing procurement security questionnaires? Email us at{" "}
                <a href="mailto:security@susdevos.com" className="text-brand-600">security@susdevos.com</a>{" "}
                and we&apos;ll respond within 3 business days.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SubProcessors() {
  const PROCESSORS = [
    { name: "Amazon Web Services", purpose: "Cloud infrastructure, database, file storage", region: "UK/EU" },
    { name: "Stripe",              purpose: "Payment processing and subscription billing",  region: "UK/EU" },
    { name: "Sentry",              purpose: "Error monitoring (PII scrubbed before upload)", region: "US (SCCs)" },
  ];

  return (
    <section className="bg-surface-50 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <h2 className="mb-3 text-2xl font-bold text-surface-900">Sub-processors</h2>
        <p className="mb-8 text-surface-500">
          The following third parties process personal data on our behalf.
          External data providers (DEFRA, Climatiq, GBIF, ECB) receive only non-personal query data.
        </p>
        <div className="overflow-hidden rounded-xl border border-surface-200 bg-white">
          <table className="w-full">
            <thead>
              <tr className="border-b border-surface-100 bg-surface-50">
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500">Processor</th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500">Purpose</th>
                <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-surface-500">Data location</th>
              </tr>
            </thead>
            <tbody>
              {PROCESSORS.map((p, i) => (
                <tr key={p.name} className={i < PROCESSORS.length - 1 ? "border-b border-surface-100" : ""}>
                  <td className="px-5 py-3.5 text-sm font-medium text-surface-900">{p.name}</td>
                  <td className="px-5 py-3.5 text-sm text-surface-600">{p.purpose}</td>
                  <td className="px-5 py-3.5 text-sm text-surface-500">{p.region}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-sm text-surface-400">
          Customers are notified 30 days before any new sub-processor is added.
          Full list available in the{" "}
          <Link href="/legal/dpa" className="text-brand-600 hover:text-brand-700 underline">DPA</Link>.
        </p>
      </div>
    </section>
  );
}

export default function SecurityPage() {
  return (
    <>
      <Hero />
      <Certifications />
      <Controls />
      <Disclosure />
      <SubProcessors />
    </>
  );
}

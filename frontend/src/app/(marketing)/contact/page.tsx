import type { Metadata } from "next";
import { Mail, MessageSquare, Shield, Newspaper } from "lucide-react";
import { ContactForm } from "./ContactForm";

export const metadata: Metadata = {
  title: "Contact — SusDevOS",
  description:
    "Get in touch with the SusDevOS team for sales, support, security, or press enquiries.",
  alternates: { canonical: "https://susdevos.com/contact" },
};

const CHANNELS = [
  {
    Icon:    MessageSquare,
    label:   "Sales & demo",
    detail:  "hello@susdevos.com",
    href:    "mailto:hello@susdevos.com",
    note:    "Pricing, trials, team plans, and platform walkthroughs. We respond within 1 business day.",
  },
  {
    Icon:    Mail,
    label:   "Support",
    detail:  "support@susdevos.com",
    href:    "mailto:support@susdevos.com",
    note:    "Questions about using the platform. Paid plan customers receive priority responses.",
  },
  {
    Icon:    Shield,
    label:   "Security",
    detail:  "security@susdevos.com",
    href:    "mailto:security@susdevos.com",
    note:    "Responsible disclosure of security vulnerabilities. We aim to respond within 24 hours.",
  },
  {
    Icon:    Newspaper,
    label:   "Press & partnerships",
    detail:  "press@susdevos.com",
    href:    "mailto:press@susdevos.com",
    note:    "Media enquiries, research partnerships, and integration discussions.",
  },
];

export default function ContactPage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <section
        className="relative overflow-hidden py-16 sm:py-20"
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
          <p className="mb-4 text-xs font-semibold uppercase tracking-widest text-brand-400">
            Get in touch
          </p>
          <h1 className="mb-4 text-4xl font-bold text-white sm:text-5xl">Contact us</h1>
          <p className="mx-auto max-w-lg text-lg text-surface-300">
            We&apos;re a small team. You&apos;ll reach a person, not a support ticket system.
          </p>
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-12 lg:grid-cols-[1fr_480px] lg:gap-16">

            {/* Left: channels */}
            <div className="space-y-4">
              <h2 className="mb-6 text-xl font-bold text-surface-900">Direct contact</h2>
              {CHANNELS.map(({ Icon, label, detail, href, note }) => (
                <a
                  key={label}
                  href={href}
                  className="group flex items-start gap-4 rounded-xl border border-surface-200 p-5 transition-all hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-md"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 transition-colors group-hover:bg-brand-100">
                    <Icon className="h-4 w-4 text-brand-600" />
                  </div>
                  <div>
                    <p className="mb-0.5 text-xs font-semibold uppercase tracking-wider text-surface-400">{label}</p>
                    <p className="mb-1 font-semibold text-brand-600">{detail}</p>
                    <p className="text-sm text-surface-500 leading-relaxed">{note}</p>
                  </div>
                </a>
              ))}

              <div className="rounded-xl border border-surface-200 bg-surface-50 p-5 mt-6">
                <p className="mb-1 font-semibold text-surface-900 text-sm">GDPR & data requests</p>
                <p className="text-sm text-surface-500">
                  For data access, erasure, or DPA enquiries, email{" "}
                  <a href="mailto:dpo@susdevos.com" className="text-brand-600 hover:text-brand-700">
                    dpo@susdevos.com
                  </a>.
                  We fulfil all GDPR data subject requests within 30 days.
                </p>
              </div>
            </div>

            {/* Right: form */}
            <div>
              <div className="rounded-2xl border border-surface-200 bg-white p-7 shadow-sm">
                <h2 className="mb-1 text-lg font-bold text-surface-900">Send a message</h2>
                <p className="mb-6 text-sm text-surface-500">We&apos;ll reply within 1 business day.</p>
                <ContactForm />
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

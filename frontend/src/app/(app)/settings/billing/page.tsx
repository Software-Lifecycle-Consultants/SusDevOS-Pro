"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";

interface Subscription {
  SubscriptionId: number;
  Status:         string;
  BillingInterval: string;
  TrialEndsAt:    string | null;
  CurrentPeriodEnd: string | null;
  PlanId: {
    PlanName:         string;
    PlanKey:          string;
    PriceMonthlyGBP:  number;
    MaxEntities:      number;
    MaxUsersPerEntity: number;
    SupportTier:      string;
  };
}

const PLAN_FEATURES: Record<string, string[]> = {
  free:         ["1 entity","1 user","Scope 1 + 2","DEFRA factors","30-day audit log"],
  starter:      ["1 entity","5 users","All scopes","All factor libraries","Carbon goals & targets","CSV export"],
  professional: ["5 entities","20 users","Verification workflow","TNFD reporting","GIS mapping"],
  agency:       ["25 entities","Unlimited users","White-label reports","Client portal"],
  enterprise:   ["Unlimited entities","SSO/SAML","Dedicated instance","99.9% SLA"],
};

const STATUS_COLOURS: Record<string, string> = {
  active:    "badge-green",
  trialing:  "badge-yellow",
  past_due:  "badge-red",
  canceled:  "badge-slate",
};

export default function BillingPage() {
  const { activeEntityId } = useAuthStore();
  const headers = activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {};

  const { data: sub, isLoading } = useQuery<Subscription>({
    queryKey: ["subscription", activeEntityId],
    queryFn: () =>
      axiosInstance.get(`/api/billing/subscription/`, { headers }).then((r) => r.data),
    enabled: !!activeEntityId,
  });

  if (isLoading) return <div className="card p-6 text-sm text-surface-500">Loading…</div>;

  if (!sub) return (
    <div className="card p-6 space-y-3">
      <p className="text-sm font-medium text-surface-800">No active subscription</p>
      <p className="text-sm text-surface-500">Your account is on the Free plan.</p>
      <Link href="/pricing" className="btn-primary inline-flex items-center gap-2 btn-sm">
        View plans <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );

  const plan = sub.PlanId;
  const features = PLAN_FEATURES[plan.PlanKey] ?? [];
  const isFree = plan.PlanKey === "free";

  return (
    <div className="space-y-4">
      {/* Current plan card */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs text-surface-400 uppercase tracking-wide font-medium mb-1">Current plan</p>
            <h2 className="text-xl font-bold text-surface-900">{plan.PlanName}</h2>
            {!isFree && (
              <p className="text-sm text-surface-500 mt-0.5">
                £{plan.PriceMonthlyGBP}/month · {sub.BillingInterval}
              </p>
            )}
          </div>
          <span className={`badge ${STATUS_COLOURS[sub.Status] ?? "badge-slate"}`}>
            {sub.Status === "trialing" ? "Trial" : sub.Status.replace("_", " ")}
          </span>
        </div>

        {sub.TrialEndsAt && (
          <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
            Trial ends {new Date(sub.TrialEndsAt).toLocaleDateString()}.
            Add a payment method to continue without interruption.
          </div>
        )}

        <ul className="space-y-2 mb-5">
          {features.map((f) => (
            <li key={f} className="flex items-center gap-2 text-sm text-surface-600">
              <CheckCircle2 className="h-4 w-4 text-brand-500 shrink-0" />
              {f}
            </li>
          ))}
        </ul>

        <div className="flex gap-3">
          {isFree ? (
            <Link href="/pricing" className="btn-primary inline-flex items-center gap-2 btn-sm">
              Upgrade <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <>
              <Link href="/pricing" className="btn-secondary btn-sm">Change plan</Link>
              <a
                href="mailto:hello@susdevos.com?subject=Billing enquiry"
                className="btn-ghost btn-sm text-surface-500"
              >
                Contact support
              </a>
            </>
          )}
        </div>
      </div>

      {/* Limits */}
      <div className="card p-6">
        <h3 className="text-sm font-semibold text-surface-800 mb-3">Plan limits</h3>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <div>
            <dt className="text-surface-500">Entities</dt>
            <dd className="font-medium text-surface-800">
              {plan.MaxEntities === 0 ? "Unlimited" : plan.MaxEntities}
            </dd>
          </div>
          <div>
            <dt className="text-surface-500">Users per entity</dt>
            <dd className="font-medium text-surface-800">
              {plan.MaxUsersPerEntity === 0 ? "Unlimited" : plan.MaxUsersPerEntity}
            </dd>
          </div>
          <div>
            <dt className="text-surface-500">Support</dt>
            <dd className="font-medium text-surface-800 capitalize">{plan.SupportTier}</dd>
          </div>
          {sub.CurrentPeriodEnd && (
            <div>
              <dt className="text-surface-500">Next renewal</dt>
              <dd className="font-medium text-surface-800">
                {new Date(sub.CurrentPeriodEnd).toLocaleDateString()}
              </dd>
            </div>
          )}
        </dl>
      </div>

      <p className="text-xs text-surface-400">
        To cancel, request a refund, or manage payment methods, contact{" "}
        <a href="mailto:hello@susdevos.com" className="text-brand-600 hover:underline">
          hello@susdevos.com
        </a>
        . Full Stripe billing UI coming soon.
      </p>
    </div>
  );
}

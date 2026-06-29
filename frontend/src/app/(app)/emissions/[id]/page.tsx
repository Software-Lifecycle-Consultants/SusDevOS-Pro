"use client";

import { useParams } from "next/navigation";
import axiosInstance from "@/lib/axios-instance";
import { DetailView, type DetailField, type DetailAction } from "@/components/DetailView";

const SCOPE_LABELS: Record<string, string> = { "1": "Scope 1 — Direct", "2": "Scope 2 — Energy", "3": "Scope 3 — Value chain" };
const VERIF_LABELS: Record<string, string> = { "1": "Unverified", "2": "Pending", "3": "Verified", "4": "Verified (3rd party)" };
const t = (v: unknown) => (v === null || v === undefined || v === "" ? "—" : `${v} tCO₂e`);

const fields: DetailField[] = [
  { key: "Title", label: "Title" },
  { key: "Scope", label: "Scope", editable: false, render: (v) => SCOPE_LABELS[String(v)] ?? String(v) },
  { key: "Scope3Category", label: "Scope 3 category", type: "number" },
  { key: "ActivityDescription", label: "Activity description", type: "textarea" },
  { key: "QuantityOrCost", label: "Quantity", type: "number" },
  { key: "Unit", label: "Unit" },
  { key: "EmissionFactor", label: "Emission factor", type: "number" },
  { key: "EmissionFactorSource", label: "EF source" },
  { key: "Gas", label: "Gas" },
  { key: "ReportingYear", label: "Reporting year", type: "number" },
  { key: "EmissionsAmountTonnes", label: "Emissions (primary)", editable: false, render: t },
  { key: "EmissionsAmountLocationBased", label: "Scope 2 — location-based (kg)", editable: false },
  { key: "EmissionsAmountMarketBased", label: "Scope 2 — market-based (kg)", editable: false },
  { key: "BiogenicCO2AmountTonnes", label: "Biogenic CO₂ (memo)", editable: false, render: t },
  { key: "VerificationStatus", label: "Verification", editable: false, render: (v) => VERIF_LABELS[String(v)] ?? String(v) },
];

export default function EmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const verified = (row: Record<string, unknown>) => Number(row.VerificationStatus) >= 3;

  const actions: DetailAction[] = [
    {
      label: "Verify",
      show: (row) => !verified(row),
      run: (_row, headers) => axiosInstance.post(`/api/emissions/${id}/verify/`, {}, { headers }),
      confirm: "Verify this record? It becomes immutable until unlocked.",
    },
    {
      label: "Unlock",
      show: (row) => verified(row),
      prompt: "Reason for unlocking this verified record:",
      run: (row, headers) =>
        axiosInstance.post(`/api/emissions/${id}/unlock/`, { reason: row.__prompt }, { headers }),
      variant: "danger",
    },
  ];

  return (
    <DetailView
      resourcePath="/api/emissions/"
      id={id}
      queryKey="emissions"
      listHref="/emissions"
      title={(r) => String(r.Title ?? "Emission record")}
      subtitle={(r) => `${SCOPE_LABELS[String(r.Scope)] ?? ""}`}
      fields={fields}
      canEdit={(r) => !verified(r)}
      canDelete={(r) => !verified(r)}
      actions={actions}
    />
  );
}

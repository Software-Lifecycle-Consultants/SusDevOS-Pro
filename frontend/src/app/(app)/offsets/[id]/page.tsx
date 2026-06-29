"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const REGISTRY_OPTIONS = [
  { value: "verra", label: "Verra (VCS)" },
  { value: "gold_standard", label: "Gold Standard" },
  { value: "other", label: "Other / Unlisted" },
];
const VALIDATION_LABELS: Record<string, string> = {
  pending: "Pending", valid: "Valid", invalid: "Invalid", unverified: "Unverified",
};

const fields: DetailField[] = [
  { key: "Title", label: "Title" },
  { key: "OffsetType", label: "Offset type" },
  { key: "Provider", label: "Provider" },
  { key: "CertificateNumber", label: "Certificate number" },
  { key: "OffsetAmountTonnes", label: "Amount (tCO₂e)", type: "number" },
  { key: "ValidFrom", label: "Valid from", type: "date" },
  { key: "ValidTo", label: "Valid to", type: "date" },
  { key: "CreditSerialNumber", label: "Credit serial number" },
  { key: "CreditRegistry", label: "Registry", type: "select", options: REGISTRY_OPTIONS },
  { key: "Remarks", label: "Remarks", type: "textarea" },
  // Server-validated (read-only)
  { key: "RegistryValidationStatus", label: "Validation status", editable: false,
    render: (v) => VALIDATION_LABELS[String(v)] ?? "—" },
  { key: "RegistryProjectName", label: "Registry project", editable: false },
  { key: "RegistryProjectType", label: "Registry project type", editable: false },
  { key: "RegistryVintageYear", label: "Vintage year", editable: false },
  { key: "RegistryRetirementBeneficiary", label: "Retirement beneficiary", editable: false },
  { key: "RegistryValidatedAt", label: "Last validated", editable: false },
];

export default function OffsetDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/emissions-offsets/"
      id={id}
      queryKey="offsets"
      listHref="/offsets"
      title={(r) => String(r.Title ?? "Carbon offset")}
      subtitle={(r) => [r.Provider, r.OffsetType].filter(Boolean).join(" · ")}
      fields={fields}
    />
  );
}

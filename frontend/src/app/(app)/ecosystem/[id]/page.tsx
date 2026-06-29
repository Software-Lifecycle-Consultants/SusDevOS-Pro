"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const fields: DetailField[] = [
  { key: "EcosystemName", label: "Name" },
  { key: "EcosystemType", label: "Type" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "AreaHectares", label: "Area (ha)", type: "number" },
];

export default function EcosystemDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/ecosystems/"
      id={id}
      queryKey="ecosystems"
      listHref="/ecosystem"
      title={(r) => String(r.EcosystemName ?? "Ecosystem")}
      fields={fields}
    />
  );
}

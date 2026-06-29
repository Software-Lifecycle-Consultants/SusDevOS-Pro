"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const t = (v: unknown) => (v === null || v === undefined || v === "" ? "—" : `${v} tCO₂e`);

const fields: DetailField[] = [
  { key: "RemovalReference", label: "Reference" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "RemovalDate", label: "Removal date", type: "date" },
  { key: "TotalTreesRemoved", label: "Trees removed", type: "number" },
  { key: "TotalBiomassCarbon", label: "Biomass carbon (server-computed)", editable: false, render: t },
  { key: "HasMitigationPlan", label: "Has mitigation plan", type: "checkbox",
    render: (v) => (v ? "Yes" : "No") },
  { key: "MitigationNotes", label: "Mitigation notes", type: "textarea" },
];

export default function TreeRemovalDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/tree-removals/"
      id={id}
      queryKey="tree-removals"
      listHref="/restorations"
      title={(r) => String(r.RemovalReference ?? `Tree removal #${r.TreeRemovalId ?? ""}`)}
      fields={fields}
    />
  );
}

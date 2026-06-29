"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const t = (v: unknown) => (v === null || v === undefined || v === "" ? "—" : `${v} tCO₂e`);

const fields: DetailField[] = [
  { key: "RestorationName", label: "Name" },
  { key: "RestorationReference", label: "Reference" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "StartDate", label: "Start date", type: "date" },
  { key: "CompletionDate", label: "Completion date", type: "date" },
  { key: "TotalAreaHectares", label: "Area (ha)", type: "number" },
  { key: "TotalTreesPlanted", label: "Trees planted", type: "number" },
  { key: "EstimatedCarbonSequestrationTonnes", label: "Sequestration (server-computed)", editable: false, render: t },
  { key: "MonitoringNotes", label: "Monitoring notes", type: "textarea" },
];

export default function RestorationDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/restorations/"
      id={id}
      queryKey="restorations"
      listHref="/restorations"
      title={(r) => String(r.RestorationName ?? "Restoration")}
      fields={fields}
    />
  );
}

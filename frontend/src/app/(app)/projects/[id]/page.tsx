"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const fields: DetailField[] = [
  { key: "ProjectName", label: "Project name" },
  { key: "ProjectReference", label: "Reference" },
  { key: "ProjectType", label: "Type" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "StartDate", label: "Start date", type: "date" },
  { key: "EndDate", label: "End date", type: "date" },
  { key: "Location", label: "Location" },
  { key: "Country", label: "Country" },
  { key: "TotalAreaHectares", label: "Area (ha)", type: "number" },
  { key: "EstimatedValueGBP", label: "Estimated value (GBP)", type: "number" },
];

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/projects/"
      id={id}
      queryKey="projects"
      listHref="/projects"
      title={(r) => String(r.ProjectName ?? "Project")}
      subtitle={(r) => [r.ProjectType, r.Country].filter(Boolean).join(" · ")}
      fields={fields}
    />
  );
}

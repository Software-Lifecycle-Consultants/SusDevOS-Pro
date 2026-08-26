"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axiosInstance from "@/lib/axios-instance";
import { useAuthStore } from "@/store/auth";
import { DetailView, type DetailField, type DetailAction } from "@/components/DetailView";

const SCOPE_LABELS: Record<string, string> = { "1": "Scope 1 — Direct", "2": "Scope 2 — Energy", "3": "Scope 3 — Value chain" };
const VERIF_LABELS: Record<string, string> = { "1": "Unverified", "2": "Pending", "3": "Verified", "4": "Verified (3rd party)" };
const tonnes = (value: unknown) =>
  value === null || value === undefined || value === "" ? "—" : `${value} tCO₂e`;

interface Project {
  ProjectId: number;
  ProjectName: string;
}

interface ProjectPhase {
  PhaseId: number;
  PhaseName: string;
  PhaseNumber: number | null;
}

interface Inventory {
  InventoryId: number;
  ReportingYear: number;
  ReportingPeriodFrom: string;
  ReportingPeriodTo: string;
  VerificationStatus: number;
}

export default function EmissionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { activeEntityId } = useAuthStore();
  const headers = useMemo(
    () => activeEntityId ? { "X-Entity-ID": String(activeEntityId) } : {},
    [activeEntityId],
  );

  const { data: record } = useQuery<Record<string, unknown>>({
    queryKey: ["emissions", id, activeEntityId],
    queryFn: () =>
      axiosInstance.get(`/api/emissions/${id}/`, { headers }).then((response) => response.data),
    enabled: Boolean(activeEntityId),
  });
  const { data: projectData } = useQuery<{ results: Project[] }>({
    queryKey: ["projects-dropdown", activeEntityId],
    queryFn: () => axiosInstance.get("/api/projects/", { headers }).then((response) => response.data),
    enabled: Boolean(activeEntityId),
  });
  const { data: inventoryData } = useQuery<{ results: Inventory[] }>({
    queryKey: ["inventories-dropdown", activeEntityId],
    queryFn: () => axiosInstance.get("/api/ghg-inventories/", { headers }).then((response) => response.data),
    enabled: Boolean(activeEntityId),
    retry: false,
  });
  const projectId = record?.ProjectId ? String(record.ProjectId) : "";
  const { data: phases = [] } = useQuery<ProjectPhase[]>({
    queryKey: ["project-phases-dropdown", activeEntityId, projectId],
    queryFn: () =>
      axiosInstance
        .get(`/api/projects/${projectId}/phases/`, { headers })
        .then((response) => response.data),
    enabled: Boolean(activeEntityId && projectId),
  });

  const projects = projectData?.results ?? [];
  const inventories = inventoryData?.results ?? [];
  const fields = useMemo<DetailField[]>(() => [
    { key: "Title", label: "Title" },
    { key: "Scope", label: "Scope", editable: false, render: (value) => SCOPE_LABELS[String(value)] ?? String(value) },
    { key: "Scope3Category", label: "Scope 3 category", type: "number" },
    {
      key: "ProjectId",
      label: "Project",
      type: "select",
      options: projects.map((project) => ({ value: project.ProjectId, label: project.ProjectName })),
      render: (value) => projects.find((project) => project.ProjectId === Number(value))?.ProjectName ?? "—",
    },
    {
      key: "PhaseId",
      label: "Project phase",
      type: "select",
      options: phases.map((phase) => ({
        value: phase.PhaseId,
        label: `${phase.PhaseNumber ? `${phase.PhaseNumber}. ` : ""}${phase.PhaseName}`,
      })),
      render: (value) => phases.find((phase) => phase.PhaseId === Number(value))?.PhaseName ?? "—",
      help: "To move a record to another project, clear its phase first, save, then select a phase from the new project.",
    },
    {
      key: "InventoryId",
      label: "Formal inventory",
      type: "select",
      options: inventories
        .filter((inventory) => inventory.VerificationStatus < 3 || inventory.InventoryId === Number(record?.InventoryId))
        .map((inventory) => ({
          value: inventory.InventoryId,
          label: `${inventory.ReportingYear} · ${inventory.ReportingPeriodFrom} to ${inventory.ReportingPeriodTo}`,
        })),
      render: (value) => {
        const inventory = inventories.find((candidate) => candidate.InventoryId === Number(value));
        return inventory
          ? `${inventory.ReportingYear} · ${inventory.ReportingPeriodFrom} to ${inventory.ReportingPeriodTo}`
          : "Unassigned";
      },
      help: "An assigned record contributes only to this inventory and must fall within its reporting period.",
    },
    { key: "ActivityDescription", label: "Activity description", type: "textarea" },
    { key: "SupplierName", label: "Supplier name" },
    { key: "ReportingPeriodFrom", label: "Period from", type: "date" },
    { key: "ReportingPeriodTo", label: "Period to", type: "date" },
    { key: "QuantityOrCost", label: "Quantity", type: "number" },
    { key: "Unit", label: "Unit" },
    { key: "EmissionFactor", label: "Emission factor", type: "number" },
    { key: "EmissionFactorSource", label: "EF source" },
    { key: "Gas", label: "Gas" },
    { key: "ReportingYear", label: "Reporting year", type: "number" },
    { key: "EmissionsAmountTonnes", label: "Emissions (primary)", editable: false, render: tonnes },
    { key: "EmissionsAmountLocationBased", label: "Scope 2 — location-based (kg)", editable: false },
    { key: "EmissionsAmountMarketBased", label: "Scope 2 — market-based (kg)", editable: false },
    { key: "BiogenicCO2AmountTonnes", label: "Biogenic CO₂ (memo)", editable: false, render: tonnes },
    { key: "VerificationStatus", label: "Verification", editable: false, render: (value) => VERIF_LABELS[String(value)] ?? String(value) },
  ], [inventories, phases, projects, record?.InventoryId]);

  const verified = (row: Record<string, unknown>) => Number(row.VerificationStatus) >= 3;
  const actions: DetailAction[] = [
    {
      label: "Verify",
      show: (row) => !verified(row),
      run: (_row, actionHeaders) => axiosInstance.post(`/api/emissions/${id}/verify/`, {}, { headers: actionHeaders }),
      confirm: "Verify this record? It becomes immutable until unlocked.",
    },
    {
      label: "Unlock",
      show: (row) => verified(row),
      prompt: "Reason for unlocking this verified record:",
      run: (row, actionHeaders) =>
        axiosInstance.post(`/api/emissions/${id}/unlock/`, { reason: row.__prompt }, { headers: actionHeaders }),
      variant: "danger",
    },
  ];

  return (
    <DetailView
      resourcePath="/api/emissions/"
      id={id}
      queryKey="emissions"
      listHref="/emissions"
      title={(row) => String(row.Title ?? "Emission record")}
      subtitle={(row) => `${SCOPE_LABELS[String(row.Scope)] ?? ""}`}
      fields={fields}
      canEdit={(row) => !verified(row)}
      canDelete={(row) => !verified(row)}
      actions={actions}
    />
  );
}

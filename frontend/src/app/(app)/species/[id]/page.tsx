"use client";

import { useParams } from "next/navigation";
import { DetailView, type DetailField } from "@/components/DetailView";

const IUCN_OPTIONS = ["LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD", "NE"].map((c) => ({ value: c, label: c }));
const FOREST_OPTIONS = ["tropical", "temperate", "boreal", "mangrove", "savanna", "shrubland", "grassland"]
  .map((c) => ({ value: c, label: c.charAt(0).toUpperCase() + c.slice(1) }));

const fields: DetailField[] = [
  { key: "CommonName", label: "Common name" },
  { key: "ScientificName", label: "Scientific name" },
  { key: "Family", label: "Family" },
  { key: "Kingdom", label: "Kingdom" },
  { key: "Description", label: "Description", type: "textarea" },
  { key: "IUCNStatus", label: "IUCN Red List status", type: "select", options: IUCN_OPTIONS },
  { key: "GBIFKey", label: "GBIF key", type: "number" },
  // IPCC biomass parameters (drive tree-removal carbon)
  { key: "IPCCForestType", label: "IPCC forest type", type: "select", options: FOREST_OPTIONS },
  { key: "BasicWoodDensity", label: "Basic wood density (D)", type: "number" },
  { key: "BiomassExpansionFactor", label: "Biomass expansion factor (BEF)", type: "number" },
  { key: "RootToShootRatio", label: "Root-to-shoot ratio (R)", type: "number" },
  { key: "CarbonFraction", label: "Carbon fraction (CF)", type: "number" },
  { key: "AnnualSequestrationRateTonnesCO2ePerHa", label: "Annual sequestration (tCO₂e/ha)", type: "number" },
  { key: "BiomassDataSource", label: "Biomass data source" },
];

export default function SpeciesDetailPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <DetailView
      resourcePath="/api/species/"
      id={id}
      queryKey="species"
      listHref="/ecosystem"
      title={(r) => String(r.CommonName ?? "Species")}
      subtitle={(r) => String(r.ScientificName ?? "")}
      fields={fields}
    />
  );
}

"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default icon paths broken by webpack
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Parcel {
  LandParcelId:    number;
  ParcelName:      string;
  AreaHectares:    string | null;
  BoundaryGeoJSON: object | null;
  LandUseType:     string | null;
}

function FitBounds({ parcels }: { parcels: Parcel[] }) {
  const map = useMap();
  useEffect(() => {
    const withGeo = parcels.filter((p) => p.BoundaryGeoJSON);
    if (!withGeo.length) return;
    try {
      // Leaflet's geoJSON accepts an array of GeoJSON objects at runtime (addData
      // iterates); the cast is through unknown because the typings only declare a
      // single GeoJsonObject parameter.
      const layer = L.geoJSON(
        withGeo.map((p) => p.BoundaryGeoJSON) as unknown as GeoJSON.GeoJsonObject,
      );
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [32, 32] });
    } catch { /* invalid GeoJSON — skip */ }
  }, [parcels, map]);
  return null;
}

export default function LandMap({ parcels }: { parcels: Parcel[] }) {
  return (
    <div className="h-[520px] w-full rounded-xl overflow-hidden border border-surface-200">
      <MapContainer
        center={[51.5, -0.09]}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds parcels={parcels} />
        {parcels.map((p) => {
          if (!p.BoundaryGeoJSON) return null;
          return (
            <GeoJSON
              key={p.LandParcelId}
              data={p.BoundaryGeoJSON as Parameters<typeof GeoJSON>[0]["data"]}
              style={{ color: "#16a34a", weight: 2, fillOpacity: 0.15 }}
              onEachFeature={(_, layer) => {
                layer.bindPopup(`
                  <strong>${p.ParcelName}</strong><br/>
                  ${p.LandUseType ?? ""}${p.AreaHectares ? ` · ${parseFloat(p.AreaHectares).toFixed(2)} ha` : ""}
                `);
              }}
            />
          );
        })}
        {/* Parcels with no geometry — show a note */}
        {parcels.some((p) => !p.BoundaryGeoJSON) && (
          <div className="leaflet-bottom leaflet-left">
            <div className="leaflet-control bg-white rounded shadow px-2 py-1 text-xs text-surface-500 m-2">
              {parcels.filter((p) => !p.BoundaryGeoJSON).length} parcel(s) have no boundary drawn
            </div>
          </div>
        )}
      </MapContainer>
    </div>
  );
}

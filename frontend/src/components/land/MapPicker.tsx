"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, GeoJSON, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  value: string;
  onChange: (geojson: string) => void;
}

function parseGeo(raw: string): { type: "point"; pos: [number, number] } | { type: "poly"; geo: object } | null {
  if (!raw.trim()) return null;
  try {
    const geo = JSON.parse(raw);
    if (geo.type === "Point" && Array.isArray(geo.coordinates)) {
      return { type: "point", pos: [geo.coordinates[1], geo.coordinates[0]] };
    }
    if (["Polygon", "MultiPolygon", "Feature", "FeatureCollection"].includes(geo.type)) {
      return { type: "poly", geo };
    }
  } catch { /* invalid */ }
  return null;
}

function FitPoly({ geo }: { geo: object }) {
  const map = useMap();
  useEffect(() => {
    try {
      const layer = L.geoJSON(geo as L.GeoJSON);
      const bounds = layer.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [32, 32] });
    } catch { /* skip */ }
  }, [geo, map]);
  return null;
}

function ClickHandler({ onClickLatLng }: { onClickLatLng: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e) => onClickLatLng(e.latlng.lat, e.latlng.lng) });
  return null;
}

export default function MapPicker({ value, onChange }: Props) {
  const parsed = parseGeo(value);

  function handleClick(lat: number, lng: number) {
    onChange(JSON.stringify({
      type: "Point",
      coordinates: [parseFloat(lng.toFixed(6)), parseFloat(lat.toFixed(6))],
    }));
  }

  return (
    <div className="h-[280px] w-full rounded-lg overflow-hidden border border-surface-200">
      <MapContainer
        center={parsed?.type === "point" ? parsed.pos : [51.5, -0.09]}
        zoom={parsed?.type === "point" ? 13 : 5}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickHandler onClickLatLng={handleClick} />
        {parsed?.type === "point" && <Marker position={parsed.pos} />}
        {parsed?.type === "poly" && (
          <>
            <GeoJSON
              data={parsed.geo as Parameters<typeof GeoJSON>[0]["data"]}
              style={{ color: "#16a34a", weight: 2, fillOpacity: 0.18 }}
            />
            <FitPoly geo={parsed.geo} />
          </>
        )}
      </MapContainer>
    </div>
  );
}

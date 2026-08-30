"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  MapContainer, TileLayer, Marker, Polygon, Polyline, GeoJSON, useMap, useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Crosshair, Loader2, Pencil, MapPin, Undo2, Trash2, Search, Check } from "lucide-react";
import axiosInstance from "@/lib/axios-instance";

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type LatLng = [number, number];
type Mode = "pin" | "draw";

interface Props {
  value: string;
  onChange: (geojson: string) => void;
  /** Live area of the drawn polygon, in hectares. null when the shape encloses none. */
  onAreaChange?: (hectares: number | null) => void;
  entityId?: number;
}

interface Place {
  DisplayName: string;
  Latitude: number;
  Longitude: number;
  BoundingBox: number[] | null;
  Type: string | null;
}

/* ── Area ────────────────────────────────────────────────────────────────────
 * Mirrors backend/apps/land/geo.py so the number the user watches while drawing
 * is the number the server stores. Spherical-excess approximation on a sphere of
 * the WGS84 semi-major axis — the same formula Leaflet's geodesicArea uses.
 */
const EARTH_RADIUS_M = 6378137;
const DEG_TO_RAD = Math.PI / 180;

function areaHectares(ring: LatLng[]): number | null {
  if (ring.length < 3) return null;
  let total = 0;
  for (let i = 0; i < ring.length; i++) {
    const [lat1, lng1] = ring[i];
    const [lat2, lng2] = ring[(i + 1) % ring.length];
    total += (lng2 - lng1) * DEG_TO_RAD * (2 + Math.sin(lat1 * DEG_TO_RAD) + Math.sin(lat2 * DEG_TO_RAD));
  }
  const m2 = Math.abs((total * EARTH_RADIUS_M * EARTH_RADIUS_M) / 2);
  return m2 > 0 ? m2 / 10_000 : null;
}

/* ── GeoJSON <-> vertices ───────────────────────────────────────────────── */

type Parsed =
  | { kind: "point"; pos: LatLng }
  | { kind: "polygon"; ring: LatLng[] }
  | { kind: "other"; geo: object }
  | null;

function parseGeo(raw: string): Parsed {
  if (!raw.trim()) return null;
  try {
    const geo = JSON.parse(raw);
    if (geo?.type === "Point" && Array.isArray(geo.coordinates)) {
      return { kind: "point", pos: [geo.coordinates[1], geo.coordinates[0]] };
    }
    if (geo?.type === "Polygon" && Array.isArray(geo.coordinates?.[0])) {
      const ring: LatLng[] = geo.coordinates[0]
        .filter((c: unknown): c is number[] => Array.isArray(c) && c.length >= 2)
        .map((c: number[]) => [c[1], c[0]] as LatLng);
      // GeoJSON closes the ring by repeating the first point; the editor does not.
      if (ring.length > 1) {
        const [aLat, aLng] = ring[0];
        const [zLat, zLng] = ring[ring.length - 1];
        if (aLat === zLat && aLng === zLng) ring.pop();
      }
      return ring.length >= 3 ? { kind: "polygon", ring } : { kind: "other", geo };
    }
    if (["MultiPolygon", "Feature", "FeatureCollection", "LineString"].includes(geo?.type)) {
      return { kind: "other", geo };
    }
  } catch { /* not JSON yet — the user may still be typing */ }
  return null;
}

function ringToGeoJSON(ring: LatLng[]): string {
  const coords = ring.map(([lat, lng]) => [round6(lng), round6(lat)]);
  coords.push(coords[0]); // close it
  return JSON.stringify({ type: "Polygon", coordinates: [coords] });
}

const round6 = (n: number) => parseFloat(n.toFixed(6));

/* ── Map plumbing ───────────────────────────────────────────────────────── */

function MapReady({ onReady }: { onReady: (map: L.Map) => void }) {
  const map = useMap();
  useEffect(() => { onReady(map); }, [map, onReady]);
  return null;
}

function ClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng.lat, e.latlng.lng) });
  return null;
}

function FitTo({ geo }: { geo: object }) {
  const map = useMap();
  useEffect(() => {
    try {
      const bounds = L.geoJSON(geo as GeoJSON.GeoJsonObject).getBounds();
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [32, 32] });
    } catch { /* skip */ }
  }, [geo, map]);
  return null;
}

const vertexIcon = L.divIcon({
  className: "",
  html: '<div style="width:11px;height:11px;border-radius:9999px;background:#16a34a;border:2px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.35)"></div>',
  iconSize: [11, 11],
  iconAnchor: [5.5, 5.5],
});

/* ── Component ──────────────────────────────────────────────────────────── */

export default function MapPicker({ value, onChange, onAreaChange, entityId }: Props) {
  const [map, setMap] = useState<L.Map | null>(null);
  const [mode, setMode] = useState<Mode>("pin");
  const [ring, setRing] = useState<LatLng[]>([]);

  const [query, setQuery] = useState("");
  const [places, setPlaces] = useState<Place[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [locating, setLocating] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  // Tracks GeoJSON this component emitted, so the sync effect below can tell an
  // external edit (the paste-GeoJSON textarea) from its own round-trip.
  const emitted = useRef<string | null>(null);

  const parsed = useMemo(() => parseGeo(value), [value]);

  const emit = useCallback((geojson: string) => {
    emitted.current = geojson;
    onChange(geojson);
  }, [onChange]);

  // Adopt an externally-set boundary: pasted GeoJSON, or an existing parcel.
  useEffect(() => {
    if (value === emitted.current) return;
    const next = parseGeo(value);
    if (next?.kind === "polygon") {
      setRing(next.ring);
      setMode("draw");
    } else if (!value.trim()) {
      setRing([]);
    }
  }, [value]);

  const liveArea = useMemo(() => {
    if (mode === "draw" && ring.length >= 3) return areaHectares(ring);
    if (parsed?.kind === "polygon") return areaHectares(parsed.ring);
    return null;
  }, [mode, ring, parsed]);

  useEffect(() => { onAreaChange?.(liveArea); }, [liveArea, onAreaChange]);

  /* Clicking the map */
  function handleMapClick(lat: number, lng: number) {
    if (mode === "pin") {
      emit(JSON.stringify({ type: "Point", coordinates: [round6(lng), round6(lat)] }));
      return;
    }
    const next: LatLng[] = [...ring, [lat, lng]];
    setRing(next);
    if (next.length >= 3) emit(ringToGeoJSON(next));
  }

  function moveVertex(index: number, lat: number, lng: number) {
    const next = ring.map((v, i) => (i === index ? ([lat, lng] as LatLng) : v));
    setRing(next);
    if (next.length >= 3) emit(ringToGeoJSON(next));
  }

  function undo() {
    const next = ring.slice(0, -1);
    setRing(next);
    if (next.length >= 3) emit(ringToGeoJSON(next));
    else emit("");
  }

  function clearAll() {
    setRing([]);
    emit("");
  }

  /* Place search */
  useEffect(() => {
    const q = query.trim();
    if (q.length < 3) { setPlaces(null); return; }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const headers = entityId ? { "X-Entity-ID": String(entityId) } : undefined;
        const { data } = await axiosInstance.get("/api/land-parcels/geocode/", {
          params: { q, limit: 6 },
          headers,
          signal: controller.signal,
        });
        setPlaces(Array.isArray(data) ? data : []);
      } catch {
        // Aborted or failed — an empty dropdown is the right outcome either way.
        setPlaces([]);
      } finally {
        setSearching(false);
      }
    }, 350);

    return () => { controller.abort(); clearTimeout(timer); };
  }, [query, entityId]);

  function goToPlace(place: Place) {
    setPlaces(null);
    setQuery(place.DisplayName.split(",")[0]);
    if (!map) return;
    const bbox = place.BoundingBox;
    if (bbox && bbox.length === 4) {
      // Nominatim order: [south, north, west, east]
      map.fitBounds([[bbox[0], bbox[2]], [bbox[1], bbox[3]]], { padding: [24, 24] });
    } else {
      map.setView([place.Latitude, place.Longitude], 13);
    }
  }

  function locateMe() {
    if (!map) return;
    if (!("geolocation" in navigator)) {
      setNotice("This browser cannot share a location.");
      return;
    }
    setLocating(true);
    setNotice(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        map.setView([pos.coords.latitude, pos.coords.longitude], 16);
      },
      (err) => {
        setLocating(false);
        setNotice(
          err.code === err.PERMISSION_DENIED
            ? "Location permission denied — search for a place instead."
            : "Could not get your location.",
        );
      },
      { enableHighAccuracy: true, timeout: 10_000, maximumAge: 60_000 },
    );
  }

  const center: LatLng =
    parsed?.kind === "point" ? parsed.pos
    : ring.length ? ring[0]
    : [51.5, -0.09];

  return (
    <div className="space-y-2">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Mode toggle */}
        <div className="flex overflow-hidden rounded-md border border-surface-200">
          <button
            type="button"
            onClick={() => setMode("pin")}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs ${
              mode === "pin" ? "bg-surface-100 text-surface-900" : "bg-white text-surface-500 hover:bg-surface-50"
            }`}
          >
            <MapPin className="h-3.5 w-3.5" /> Pin
          </button>
          <button
            type="button"
            onClick={() => setMode("draw")}
            className={`flex items-center gap-1.5 border-l border-surface-200 px-2.5 py-1.5 text-xs ${
              mode === "draw" ? "bg-surface-100 text-surface-900" : "bg-white text-surface-500 hover:bg-surface-50"
            }`}
          >
            <Pencil className="h-3.5 w-3.5" /> Draw area
          </button>
        </div>

        {/* Place search */}
        <div className="relative min-w-[180px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-surface-400" />
          <input
            type="text"
            className="input h-[34px] w-full pl-8 text-xs"
            placeholder="Search for a city, town or address…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            // The form's submit must not fire when picking a place with Enter.
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                if (places?.length) goToPlace(places[0]);
              }
            }}
          />
          {searching && (
            <Loader2 className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 animate-spin text-surface-400" />
          )}
          {places && places.length > 0 && (
            <ul className="absolute z-[1000] mt-1 max-h-56 w-full overflow-auto rounded-md border border-surface-200 bg-white py-1 shadow-lg">
              {places.map((p, i) => (
                <li key={`${p.Latitude},${p.Longitude},${i}`}>
                  <button
                    type="button"
                    onClick={() => goToPlace(p)}
                    className="block w-full px-3 py-1.5 text-left text-xs text-surface-700 hover:bg-surface-50"
                  >
                    {p.DisplayName}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {places && places.length === 0 && query.trim().length >= 3 && !searching && (
            <div className="absolute z-[1000] mt-1 w-full rounded-md border border-surface-200 bg-white px-3 py-2 text-xs text-surface-400 shadow-lg">
              No places found.
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={locateMe}
          disabled={locating || !map}
          className="btn-secondary btn-sm flex items-center gap-1.5 text-xs"
          title="Centre the map on your current location"
        >
          {locating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Crosshair className="h-3.5 w-3.5" />}
          My location
        </button>
      </div>

      {/* Drawing controls */}
      {mode === "draw" && (
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button" onClick={undo} disabled={!ring.length}
            className="btn-secondary btn-sm flex items-center gap-1.5 text-xs"
          >
            <Undo2 className="h-3.5 w-3.5" /> Undo point
          </button>
          <button
            type="button" onClick={clearAll} disabled={!ring.length}
            className="btn-secondary btn-sm flex items-center gap-1.5 text-xs"
          >
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </button>
          <span className="text-xs text-surface-400">
            {ring.length === 0 && "Click the map to place the first corner."}
            {ring.length > 0 && ring.length < 3 &&
              `${ring.length} of 3 corners — keep clicking to close the shape.`}
            {ring.length >= 3 && `${ring.length} corners · drag any point to adjust.`}
          </span>
          {liveArea !== null && (
            <span className="ml-auto flex items-center gap-1.5 rounded-md border border-brand-100 bg-brand-50 px-2 py-1 text-xs font-medium text-brand-700">
              <Check className="h-3.5 w-3.5" />
              {liveArea.toLocaleString(undefined, { maximumFractionDigits: 2 })} ha
            </span>
          )}
        </div>
      )}

      {/* Map */}
      <div className="h-[280px] w-full overflow-hidden rounded-lg border border-surface-200">
        <MapContainer
          center={center}
          zoom={parsed?.kind === "point" || ring.length ? 13 : 5}
          style={{ height: "100%", width: "100%" }}
        >
          <MapReady onReady={setMap} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickHandler onClick={handleMapClick} />

          {mode === "pin" && parsed?.kind === "point" && <Marker position={parsed.pos} />}

          {mode === "draw" && ring.length >= 3 && (
            <Polygon positions={ring} pathOptions={{ color: "#16a34a", weight: 2, fillOpacity: 0.18 }} />
          )}
          {mode === "draw" && ring.length === 2 && (
            <Polyline positions={ring} pathOptions={{ color: "#16a34a", weight: 2, dashArray: "4 4" }} />
          )}
          {mode === "draw" && ring.map((pos, i) => (
            <Marker
              key={i}
              position={pos}
              icon={vertexIcon}
              draggable
              eventHandlers={{
                dragend: (e) => {
                  const { lat, lng } = (e.target as L.Marker).getLatLng();
                  moveVertex(i, lat, lng);
                },
              }}
            />
          ))}

          {/* Geometry we cannot edit in place (MultiPolygon, Feature…) is still shown. */}
          {parsed?.kind === "other" && (
            <>
              <GeoJSON
                data={parsed.geo as Parameters<typeof GeoJSON>[0]["data"]}
                style={{ color: "#16a34a", weight: 2, fillOpacity: 0.18 }}
              />
              <FitTo geo={parsed.geo} />
            </>
          )}
        </MapContainer>
      </div>

      {notice && <p className="text-xs text-amber-600">{notice}</p>}
    </div>
  );
}

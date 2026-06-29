"use client";

/**
 * Entity switcher for multi-entity users (G21). Lists the entities the current
 * user can access (/api/entities/accessible/ — primary + EntityMembers grants,
 * or all entities for SuperAdmin) and switches the active tenant context, which
 * drives the X-Entity-ID header on every subsequent request.
 *
 * Renders nothing unless the user has access to more than one entity.
 */
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import axiosInstance from "@/lib/axios-instance";

interface AccessibleEntity {
  EntityId: number;
  EntityName: string;
  IsPrimary: boolean;
}

export function EntitySwitcher() {
  const { activeEntityId, setActiveEntityId } = useAuthStore();

  const { data } = useQuery<AccessibleEntity[]>({
    queryKey: ["accessible-entities"],
    queryFn: () => axiosInstance.get("/api/entities/accessible/").then((r) => r.data),
    staleTime: 5 * 60_000,
  });

  const entities = data ?? [];
  if (entities.length < 2) return null; // nothing to switch between

  return (
    <select
      className="input h-8 max-w-[200px] py-0 text-sm"
      value={activeEntityId ?? ""}
      onChange={(e) => setActiveEntityId(Number(e.target.value))}
      aria-label="Active entity"
    >
      {entities.map((e) => (
        <option key={e.EntityId} value={e.EntityId}>
          {e.EntityName}{e.IsPrimary ? " (primary)" : ""}
        </option>
      ))}
    </select>
  );
}

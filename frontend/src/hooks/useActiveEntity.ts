/**
 * Returns the activeEntityId from the auth store with a safe-access wrapper.
 * Use this instead of calling useAuthStore directly in components.
 */
import { useAuthStore } from "@/store/auth";

export function useActiveEntity() {
  const activeEntityId = useAuthStore((s) => s.activeEntityId);
  const entityId       = useAuthStore((s) => s.user?.entity_id ?? null);
  const setActive      = useAuthStore((s) => s.setActiveEntityId);

  return {
    activeEntityId: activeEntityId ?? entityId,
    setActiveEntityId: setActive,
  };
}

/**
 * Zustand auth store.
 * Holds the JWT access token (in memory only — never localStorage).
 * The refresh token lives in an HttpOnly cookie managed by the browser.
 */
import { create } from "zustand";

export interface AuthUser {
  UserId:           number;
  email:            string;
  username:         string;
  FirstName:        string;
  LastName:         string;
  IsSuperAdmin:     boolean;
  entity_id:        number | null;
  role:             string | null;
}

interface AuthState {
  accessToken:    string | null;
  activeEntityId: number | null;
  user:           AuthUser | null;
  privileges:     Record<string, boolean>;

  setAccessToken:    (token: string) => void;
  setUser:           (user: AuthUser) => void;
  setPrivileges:     (p: Record<string, boolean>) => void;
  setActiveEntityId: (id: number) => void;
  clearAuth:         () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken:    null,
  activeEntityId: null,
  user:           null,
  privileges:     {},

  setAccessToken: (token) => set({ accessToken: token }),

  setUser: (user) =>
    set({
      user,
      activeEntityId: user.entity_id ?? null,
    }),

  setPrivileges: (privileges) => set({ privileges }),

  setActiveEntityId: (id) => set({ activeEntityId: id }),

  clearAuth: () => set({ accessToken: null, activeEntityId: null, user: null, privileges: {} }),
}));

/** Derived helper — display name with fallback to username */
export function displayName(user: AuthUser | null): string {
  if (!user) return "";
  if (user.FirstName || user.LastName) {
    return [user.FirstName, user.LastName].filter(Boolean).join(" ");
  }
  return user.username;
}

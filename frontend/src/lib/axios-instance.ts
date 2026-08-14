/**
 * Axios instance used by all orval-generated API hooks.
 * Handles: base URL, JWT Bearer token, X-Entity-ID header,
 * automatic token refresh on 401.
 */
import axios, { type AxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";

// Browser requests must be same-origin ("" → /api/... on the current host):
// Nginx routes /api/ to Django in production, and the Next.js rewrite proxies
// it in dev. NEXT_PUBLIC_API_URL (e.g. http://api:8000 inside Docker) is only
// resolvable server-side — baking it into the browser bundle breaks every call.
const baseURL =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    : "";

export const axiosInstance = axios.create({
  baseURL,
  withCredentials: true,       // send HttpOnly refresh cookie
  headers: { "Content-Type": "application/json" },
});

// Attach access token and active entity ID to every request
axiosInstance.interceptors.request.use((config) => {
  const { accessToken, activeEntityId } = useAuthStore.getState();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  if (activeEntityId) {
    config.headers["X-Entity-ID"] = String(activeEntityId);
  }
  return config;
});

// On 401: attempt silent token refresh, then retry once
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const { data } = await axios.post(
          "/api/auth/refresh",
          {},
          { withCredentials: true }
        );
        useAuthStore.getState().setAccessToken(data.access_token);
        original.headers = {
          ...original.headers,
          Authorization: `Bearer ${data.access_token}`,
        };
        return axiosInstance(original);
      } catch {
        useAuthStore.getState().clearAuth();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;

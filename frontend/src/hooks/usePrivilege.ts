/**
 * usePrivilege — check whether a feature is accessible on the current plan.
 *
 * Usage:
 *   const { allowed, upgradeUrl } = usePrivilege("bulk_import");
 *   if (!allowed) return <UpgradePrompt href={upgradeUrl} />;
 *
 * When the API returns HTTP 403 with { code: "feature_gated", feature: "..." }
 * the hook catches that shape and treats it as "not allowed."
 */
import { AxiosError } from "axios";

interface GateError {
  code:         "feature_gated";
  feature:      string;
  current_plan: string;
  upgrade_url:  string;
  message:      string;
}

export interface PrivilegeInfo {
  allowed:     boolean;
  upgradeUrl:  string;
  featureKey:  string | null;
  currentPlan: string | null;
  message:     string | null;
}

/**
 * Parse an AxiosError to see if it is a feature-gate 403.
 * Returns PrivilegeInfo with allowed=false if it is, null otherwise.
 */
export function parseGateError(err: unknown): PrivilegeInfo | null {
  if (!(err instanceof AxiosError)) return null;
  const data = err.response?.data as Partial<GateError> | undefined;
  if (err.response?.status !== 402 || data?.code !== "feature_gated") return null;

  return {
    allowed:     false,
    upgradeUrl:  data.upgrade_url  ?? "/settings/billing",
    featureKey:  data.feature      ?? null,
    currentPlan: data.current_plan ?? null,
    message:     data.message      ?? "Upgrade your plan to access this feature.",
  };
}

/**
 * Standalone hook for components that pre-check access before mounting a view.
 * Pass the AxiosError (if any) from a mutation or query error prop.
 */
export function usePrivilege(err: unknown): PrivilegeInfo {
  const gateInfo = parseGateError(err);
  if (gateInfo) return gateInfo;
  return { allowed: true, upgradeUrl: "/settings/billing", featureKey: null, currentPlan: null, message: null };
}

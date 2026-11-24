import { ApiError, AuthRequiredError } from "./api-client";

export interface RuleSetting {
  name: string;
  default: number;
  current: number;
  changed: boolean;
  implemented: boolean;
}

export interface BandInfo {
  name: string;
  action: string;
  min: number;
  max: number;
}

export interface SettingsHistory {
  id: number;
  at: string;
  actor: string;
  key: string;
  old_value: string | null;
  new_value: string | null;
  reason: string;
}

export interface SettingsView {
  max_points: number;
  rules: RuleSetting[];
  cutoffs: { current: number[]; default: number[] };
  bands: BandInfo[];
  history: SettingsHistory[];
}

export interface PreviewResult {
  scans_checked: number;
  before: Record<string, number>;
  after: Record<string, number>;
  changed_count: number;
  changed: { scan_id: string; url: string; old_score: number; new_score: number; old_band: string; new_band: string }[];
}

export async function call<T>(path: string, method = "GET", json?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      cache: "no-store",
      headers: json === undefined ? undefined : { "Content-Type": "application/json" },
      body: json === undefined ? undefined : JSON.stringify(json),
    });
  } catch {
    throw new ApiError("Could not reach the Manee service.");
  }
  if (!res.ok) {
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = "Please check the values you entered.";
    } catch {
      /* not JSON */
    }
    if (res.status === 401 || res.status === 403) throw new AuthRequiredError(detail || "This needs an administrator.");
    throw new ApiError(detail || "The service returned an error.");
  }
  return (await res.json()) as T;
}

export const fetchSettings = () => call<SettingsView>("/api/v1/admin/settings");

export const saveRule = (name: string, points: number, reason: string) =>
  call<SettingsView>(`/api/v1/admin/settings/rules/${encodeURIComponent(name)}`, "PUT", { points, reason });

export const saveCutoffs = (cut: number[], reason: string) =>
  call<SettingsView>("/api/v1/admin/settings/cutoffs", "PUT", {
    suspicious: cut[0],
    high_risk: cut[1],
    likely_fraud: cut[2],
    reason,
  });

export const resetSettings = (reason: string) => call<SettingsView>("/api/v1/admin/settings/reset", "POST", { reason });

export const previewSettings = (rules: Record<string, number>, cutoffs: number[] | null) =>
  call<PreviewResult>("/api/v1/admin/settings/preview", "POST", { rules, cutoffs });

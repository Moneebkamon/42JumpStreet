import { call } from "./api-admin";

export interface FlaggedSafe {
  scan_id: string;
  url: string;
  host: string;
  score: number;
  band: string;
  created_at: string;
  feedback_at: string | null;
  already_allowlisted: boolean;
  shared_hosting: boolean;
}

export interface AllowlistEntry {
  host: string;
  reason: string;
  added_by: string;
  added_at: string;
  source_scan_id: string | null;
}

export const fetchReviewQueue = () => call<FlaggedSafe[]>("/api/v1/admin/feedback");
export const fetchAllowlist = () => call<AllowlistEntry[]>("/api/v1/admin/allowlist");

export const promoteFeedback = (scanId: string, reason: string) =>
  call<{ host: string }>(`/api/v1/admin/feedback/${encodeURIComponent(scanId)}/promote`, "POST", { reason });

export const dismissFeedback = (scanId: string, reason: string) =>
  call<{ host: string }>(`/api/v1/admin/feedback/${encodeURIComponent(scanId)}/dismiss`, "POST", { reason });

export const removeAllowlisted = (host: string, reason: string) =>
  call<{ host: string }>(`/api/v1/admin/allowlist/${encodeURIComponent(host)}?reason=${encodeURIComponent(reason)}`, "DELETE");

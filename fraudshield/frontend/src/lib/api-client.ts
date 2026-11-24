import type { CheckedItem, DiscoveryStats, FeedFilters, FeedItem } from "@/types/feed";
import type { ScanResult, ScanSummary, StoredScan, Verdict } from "@/types/scan";

export class ApiError extends Error {}
/** The service says this needs a signed-in staff member (401) or more rights (403). */
export class AuthRequiredError extends ApiError {}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { signal, cache: "no-store" });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the Manee service.");
  }
  if (res.status === 401 || res.status === 403) throw new AuthRequiredError("Please sign in with a staff account.");
  if (!res.ok) throw new ApiError("The service returned an error.");
  return (await res.json()) as T;
}

export function fetchFeed(filters: FeedFilters, signal?: AbortSignal): Promise<FeedItem[]> {
  const q = new URLSearchParams({ min_score: String(filters.minScore), limit: "100" });
  if (filters.brand) q.set("brand", filters.brand);
  return getJson<FeedItem[]>(`/api/v1/feed?${q}`, signal);
}

export function fetchStats(signal?: AbortSignal): Promise<DiscoveryStats> {
  return getJson<DiscoveryStats>("/api/v1/stats", signal);
}

export function fetchChecked(signal?: AbortSignal): Promise<CheckedItem[]> {
  return getJson<CheckedItem[]>("/api/v1/checked?limit=300", signal);
}

/** The one place the frontend talks to the backend. */
export async function scanUrl(
  url: string,
  { deep = false, signal }: { deep?: boolean; signal?: AbortSignal } = {},
): Promise<ScanResult> {
  let res: Response;
  try {
    res = await fetch("/api/v1/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, deep }),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the Manee service. Please try again.");
  }

  if (res.status === 422) {
    throw new ApiError("That doesn't look like a valid link. Check it and try again.");
  }
  if (res.status === 401) {
    throw new AuthRequiredError("Opening the page in the safe browser is for signed-in staff. Sign in, or untick that option.");
  }
  if (res.status === 403) {
    throw new AuthRequiredError("Deep search is for staff accounts. Untick that option to run a normal check.");
  }
  if (res.status === 429) {
    throw new ApiError("Too many scans in a short time. Please wait a minute and try again.");
  }
  if (!res.ok) {
    throw new ApiError("The scan failed on our side. Please try again.");
  }
  return (await res.json()) as ScanResult;
}

export class NotFoundError extends ApiError {}

export function fetchScans(signal?: AbortSignal): Promise<ScanSummary[]> {
  return getJson<ScanSummary[]>("/api/v1/scans?limit=100", signal);
}

export async function fetchScan(scanId: string, signal?: AbortSignal): Promise<StoredScan> {
  let res: Response;
  try {
    res = await fetch(`/api/v1/scan/${encodeURIComponent(scanId)}`, { signal, cache: "no-store" });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the Manee service.");
  }
  if (res.status === 404) throw new NotFoundError("We could not find that scan.");
  if (!res.ok) throw new ApiError("The service returned an error.");
  return (await res.json()) as StoredScan;
}

export async function sendVerdict(scanId: string, label: Verdict): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`/api/v1/scan/${encodeURIComponent(scanId)}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label }),
    });
  } catch {
    throw new ApiError("Could not reach the Manee service.");
  }
  if (!res.ok) throw new ApiError("Could not save your answer. Please try again.");
}

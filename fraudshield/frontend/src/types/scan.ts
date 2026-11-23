// Mirrors backend/app/schemas/scan.py

export type Band = "safe" | "suspicious" | "high_risk" | "likely_fraud";

export interface Reason {
  rule: string;
  points: number;
  reason: string;
}

/** What the sandbox browser saw. Present only for a deep scan that could open the page. */
export interface ScanPage {
  final_url: string;
  title: string;
  status: number | null;
  redirect_chain: string[];
  network_hosts: string[];
  blocked_hosts: string[];
  contacts: { phones: string[]; wallets: string[]; handles: string[] };
  truncated: boolean;
}

export interface ScanResult {
  scan_id: string;
  state: "queued" | "running" | "complete" | "failed";
  url: string;
  score: number;
  band: Band;
  action: string;
  confidence: number;
  reasons: Reason[];
  analyzers_ok: string[];
  analyzers_failed: string[];
  features: Record<string, string | number | null>;
  explanation?: string;
  page: ScanPage | null;
}

export type Verdict = "scam" | "safe";

/** A scan fetched back from storage (GET /api/v1/scan/{id}). Mirrors StoredScan in the backend. */
export interface StoredScan extends ScanResult {
  created_at: string;
  feedback: Verdict | null;
}

/** One row of the history list (GET /api/v1/scans). */
export interface ScanSummary {
  scan_id: string;
  url: string;
  score: number;
  band: Band;
  action: string;
  deep: boolean;
  cached: boolean;
  created_at: string;
  feedback: Verdict | null;
}

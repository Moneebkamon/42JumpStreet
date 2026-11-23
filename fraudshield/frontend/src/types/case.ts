// Mirrors the stage 09 backend (cases, evidence, takedown drafts, queue, audit).
import type { Band, Reason } from "@/types/scan";

export type CaseStatus =
  | "new"
  | "under_review"
  | "confirmed"
  | "takedown_requested"
  | "taken_down"
  | "closed"
  | "false_positive";

export interface CaseSummary {
  ref: string;
  title: string;
  url: string;
  host: string;
  source: "scan" | "detection" | "report";
  status: CaseStatus;
  priority: number;
  score: number;
  band: Band;
  brand_id: string;
  brand_name: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CaseEvent {
  id: number;
  kind: "created" | "status" | "note" | "evidence" | "takedown_draft";
  actor: string;
  text: string;
  from_status: CaseStatus | null;
  to_status: CaseStatus | null;
  at: string;
}

export interface EvidenceItem {
  id: number;
  case_ref: string;
  kind: string;
  sha256: string;
  captured_at: string;
  tool_version: string;
  captured_by: string;
  size_bytes: number;
}

export interface EvidenceContent extends EvidenceItem {
  content: string;
}

export interface EvidenceCheck {
  id: number;
  ok: boolean;
  stored_sha256: string;
  recomputed_sha256: string;
}

export interface DraftSummary {
  id: number;
  case_ref: string;
  recipient_type: string;
  subject: string;
  created_by: string;
  created_at: string;
  exported_at: string | null;
}

export interface Draft extends DraftSummary {
  body: string;
}

export interface CaseDetail extends CaseSummary {
  result: { reasons: Reason[] } & Record<string, unknown>;
  events: CaseEvent[];
  evidence: EvidenceItem[];
  takedown_drafts: DraftSummary[];
  allowed_next: CaseStatus[];
}

export interface QueueItem {
  kind: "detection" | "report";
  ref: string;
  url: string;
  host: string;
  score: number;
  band: Band;
  brand_name: string;
  when: string;
  priority: number;
  reports: number;
}

export interface AuditEntry {
  id: number;
  at: string;
  actor: string;
  action: string;
  object_type: string;
  object_id: string;
  detail: string;
}

export interface ReportReceipt {
  ref: string;
  score: number;
  band: Band;
  advice: string;
}

import type {
  AuditEntry,
  CaseDetail,
  CaseStatus,
  CaseSummary,
  Draft,
  EvidenceCheck,
  EvidenceContent,
  EvidenceItem,
  QueueItem,
  ReportReceipt,
} from "@/types/case";

import { ApiError, AuthRequiredError } from "./api-client";

/** The service said "this clashes with current state" (e.g. a case for the domain is already open). */
export class ConflictError extends ApiError {
  ref: string | null;
  constructor(message: string, ref: string | null) {
    super(message);
    this.ref = ref;
  }
}

async function call<T>(path: string, init?: RequestInit & { json?: unknown }, signal?: AbortSignal): Promise<T> {
  const { json, ...rest } = init ?? {};
  let res: Response;
  try {
    res = await fetch(path, {
      cache: "no-store",
      signal,
      ...rest,
      headers: json === undefined ? rest.headers : { "Content-Type": "application/json", ...rest.headers },
      body: json === undefined ? rest.body : JSON.stringify(json),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the FraudShield service.");
  }
  if (!res.ok) {
    let detail = "";
    let ref: string | null = null;
    try {
      const body = (await res.json()) as { detail?: unknown; ref?: string | null };
      detail = typeof body.detail === "string" ? body.detail : "";
      ref = body.ref ?? null;
    } catch {
      /* not JSON: keep the generic message */
    }
    if (res.status === 401 || res.status === 403) throw new AuthRequiredError(detail || "Please sign in with a staff account.");
    if (res.status === 409) throw new ConflictError(detail || "That action is not allowed right now.", ref);
    if (res.status === 429) throw new ApiError(detail || "Too many requests. Please try again later.");
    throw new ApiError(detail || "The service returned an error.");
  }
  const type = res.headers.get("content-type") ?? "";
  return (type.includes("json") ? await res.json() : await res.text()) as T;
}

export const fetchQueue = (signal?: AbortSignal) => call<QueueItem[]>("/api/v1/queue?limit=50", undefined, signal);

export const fetchCases = (status: string, signal?: AbortSignal) =>
  call<CaseSummary[]>(`/api/v1/cases${status ? `?status=${encodeURIComponent(status)}` : ""}`, undefined, signal);

export const fetchCase = (ref: string, signal?: AbortSignal) =>
  call<CaseDetail>(`/api/v1/cases/${encodeURIComponent(ref)}`, undefined, signal);

export const openCase = (source: "scan" | "detection" | "report", sourceRef: string) =>
  call<CaseDetail>("/api/v1/cases", { method: "POST", json: { source, source_ref: sourceRef } });

export const changeStatus = (ref: string, toStatus: CaseStatus, reason: string) =>
  call<CaseDetail>(`/api/v1/cases/${encodeURIComponent(ref)}`, { method: "PATCH", json: { to_status: toStatus, reason } });

export const addNote = (ref: string, text: string) =>
  call<CaseDetail>(`/api/v1/cases/${encodeURIComponent(ref)}/notes`, { method: "POST", json: { text } });

export const freezeEvidence = (ref: string) =>
  call<EvidenceItem[]>(`/api/v1/cases/${encodeURIComponent(ref)}/evidence`, { method: "POST" });

export const viewEvidence = (id: number) => call<EvidenceContent>(`/api/v1/evidence/${id}`);

export const verifyEvidence = (id: number) => call<EvidenceCheck>(`/api/v1/evidence/${id}/verify`);

export const fetchRecipients = () => call<Record<string, string>>("/api/v1/takedown-recipients");

export const createDraft = (ref: string, recipientType: string) =>
  call<Draft>(`/api/v1/cases/${encodeURIComponent(ref)}/takedown-drafts`, { method: "POST", json: { recipient_type: recipientType } });

export const fetchDraft = (id: number) => call<Draft>(`/api/v1/takedowns/${id}`);

export const draftExportUrl = (id: number) => `/api/v1/takedowns/${id}/export`;

export const submitReport = (payload: { url: string; note: string; contact: string; website: string }) =>
  call<ReportReceipt>("/api/v1/citizen-reports", { method: "POST", json: payload });

export const fetchAudit = (signal?: AbortSignal) => call<AuditEntry[]>("/api/v1/audit?limit=200", undefined, signal);

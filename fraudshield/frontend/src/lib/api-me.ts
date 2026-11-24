import { ApiError, AuthRequiredError } from "./api-client";
import type { Band } from "@/types/scan";

export interface Summary {
  username: string;
  role: string;
  settings: UserSettings;
  scans: number;
  risky_scans: number;
  visits: number;
  risky_visits: number;
  messages: number;
  blocked: number;
  contacts: number;
  devices: number;
}
export interface UserSettings {
  extension_enabled: boolean;
  alerts_enabled: boolean;
}
export interface HistoryItem {
  url: string;
  score: number;
  band: Band;
  source: "manual" | "extension" | "message";
  created_at: string;
  scan_id: string | null;
}
export type ContactKind = "email" | "phone" | "whatsapp";
export interface Contact {
  id: number;
  kind: ContactKind;
  value: string;
  verified: boolean;
}
export interface GuardedMessage {
  id: number;
  channel: "sms" | "whatsapp";
  sender: string;
  contact_value: string;
  links: { url: string; band: Band; score: number; reasons: string[] }[];
  worst_band: Band;
  action: "blocked" | "monitor" | "allowed";
  emailed: boolean;
  created_at: string;
}
export interface Device {
  id: number;
  label: string;
  created_at: string;
  last_seen: string | null;
}

async function call<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1/me${path}`, {
      ...init,
      signal,
      cache: "no-store",
      headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Could not reach the Manee service.");
  }
  if (res.status === 401) throw new AuthRequiredError("Please sign in.");
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    throw new ApiError(typeof body?.detail === "string" ? body.detail : "The service returned an error.");
  }
  return (await res.json()) as T;
}

export const fetchSummary = (s?: AbortSignal) => call<Summary>("/summary", undefined, s);
export const putSettings = async (patch: Partial<UserSettings>) => {
  const saved = await call<UserSettings>("/settings", { method: "PUT", body: JSON.stringify(patch) });
  // The Manee extension (when installed) listens for this and re-reads its on/off switch at once.
  if (typeof window !== "undefined") window.postMessage({ source: "manee-site", type: "settings-changed" }, window.location.origin);
  return saved;
};
export const fetchHistory = (source: string, s?: AbortSignal) =>
  call<HistoryItem[]>(`/history?limit=200${source ? `&source=${source}` : ""}`, undefined, s);
export const clearHistory = () => call<{ deleted: number }>("/history", { method: "DELETE" });
export const fetchContacts = (s?: AbortSignal) => call<Contact[]>("/contacts", undefined, s);
export const addContact = (kind: ContactKind, value: string) => call<Contact>("/contacts", { method: "POST", body: JSON.stringify({ kind, value }) });
export const removeContact = (id: number) => call<{ ok: boolean }>(`/contacts/${id}`, { method: "DELETE" });
export const fetchAlerts = (s?: AbortSignal) => call<GuardedMessage[]>("/alerts", undefined, s);
export const fetchDevices = (s?: AbortSignal) => call<Device[]>("/devices", undefined, s);
export const createDevice = (label: string) => call<{ id: number; token: string }>("/devices", { method: "POST", body: JSON.stringify({ label }) });
export const removeDevice = (id: number) => call<{ ok: boolean }>(`/devices/${id}`, { method: "DELETE" });

export interface WhatsAppState {
  available: boolean;
  linked: boolean;
  status: "none" | "connecting" | "open";
  number: string | null;
  qr: string | null;
  pairing_code: string | null;
}
export const fetchWhatsApp = (s?: AbortSignal) => call<WhatsAppState>("/whatsapp/status", undefined, s);
export const connectWhatsApp = (number: string) => call<WhatsAppState>("/whatsapp/connect", { method: "POST", body: JSON.stringify({ number }) });
export const refreshWhatsApp = () => call<WhatsAppState>("/whatsapp/refresh", { method: "POST" });
export const disconnectWhatsApp = () => call<WhatsAppState>("/whatsapp", { method: "DELETE" });

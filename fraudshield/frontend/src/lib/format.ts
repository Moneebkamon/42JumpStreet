import type { Band } from "@/types/scan";

// Full class names (not built dynamically) so Tailwind can see them.
export const BAND_META: Record<
  Band,
  { label: string; summary: string; badge: string; stroke: string }
> = {
  safe: {
    label: "Looks safe",
    summary: "No warning signs found in the link or domain.",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    stroke: "stroke-emerald-500",
  },
  suspicious: {
    label: "Suspicious",
    summary: "Some warning signs. Do not enter passwords or card details.",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
    stroke: "stroke-amber-500",
  },
  high_risk: {
    label: "High risk",
    summary: "Several strong warning signs. Do not open this link.",
    badge: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
    stroke: "stroke-orange-500",
  },
  likely_fraud: {
    label: "Likely fraud",
    summary: "This link very likely belongs to a scam. Do not open it.",
    badge: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
    stroke: "stroke-red-500",
  },
};

export const CHECK_LABELS: Record<string, string> = {
  lexical: "link structure",
  homoglyph: "look-alike characters",
  shortener: "link shorteners",
  brand: "brand impersonation",
  domain_intel: "domain registration and certificate",
  sandbox: "page opened in a safe browser",
  forms: "login and payment forms",
  text_signals: "pressure and profit language",
  resources: "hidden frames and scripts",
  contacts: "phone numbers, wallets and chat handles",
  redirects: "redirects",
  page_brand: "brand shown on the page",
};

export function describeDays(days: number): string {
  if (days < 1) return "today";
  if (days === 1) return "1 day";
  if (days < 60) return `${days} days`;
  if (days < 730) return `${Math.round(days / 30)} months`;
  return `${Math.floor(days / 365)} years`;
}

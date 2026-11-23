import type { CaseStatus } from "@/types/case";

export const STATUS_LABEL: Record<CaseStatus, string> = {
  new: "New",
  under_review: "Under review",
  confirmed: "Confirmed",
  takedown_requested: "Takedown requested",
  taken_down: "Taken down",
  closed: "Closed",
  false_positive: "False positive",
};

export const STATUS_BADGE: Record<CaseStatus, string> = {
  new: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
  under_review: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  confirmed: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  takedown_requested: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
  taken_down: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  closed: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  false_positive: "bg-violet-100 text-violet-800 dark:bg-violet-950 dark:text-violet-300",
};

/** The normal path, left to right (false positive is a side exit, not a step). */
export const STATUS_PATH: CaseStatus[] = ["new", "under_review", "confirmed", "takedown_requested", "taken_down", "closed"];

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { VerdictBadge } from "@/components/results/verdict-badge";
import { usePolling } from "@/hooks/use-polling";
import { fetchCases } from "@/lib/api-cases";
import { STATUS_BADGE, STATUS_LABEL, formatTime } from "@/lib/labels";
import type { CaseStatus } from "@/types/case";

const FILTERS: { value: "" | CaseStatus; label: string }[] = [
  { value: "", label: "All cases" },
  { value: "new", label: STATUS_LABEL.new },
  { value: "under_review", label: STATUS_LABEL.under_review },
  { value: "confirmed", label: STATUS_LABEL.confirmed },
  { value: "takedown_requested", label: STATUS_LABEL.takedown_requested },
  { value: "taken_down", label: STATUS_LABEL.taken_down },
  { value: "closed", label: STATUS_LABEL.closed },
  { value: "false_positive", label: STATUS_LABEL.false_positive },
];

export function CaseList() {
  const [status, setStatus] = useState<"" | CaseStatus>("");
  const fetcher = useCallback((signal: AbortSignal) => fetchCases(status, signal), [status]);
  const { data, error, loaded } = usePolling(fetcher, 8000);

  return (
    <div className="space-y-4">
      <label className="block space-y-1 text-xs text-zinc-500">
        <span>Status</span>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as "" | CaseStatus)}
          className="block rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        >
          {FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </label>

      {!loaded ? (
        <p role="status" className="text-sm text-zinc-500">
          Loading cases...
        </p>
      ) : !data ? (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {error ?? "Could not load the cases."}
        </p>
      ) : data.length === 0 ? (
        <p className="rounded-xl border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-700">
          No cases here yet. Open one from the{" "}
          <Link href="/console" className="underline">
            early detection queue
          </Link>{" "}
          or from a scan.
        </p>
      ) : (
        <div className="max-h-96 overflow-auto glass rounded-xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
              <tr>
                <th className="px-3 py-2">Case</th>
                <th className="px-3 py-2">Address</th>
                <th className="px-3 py-2">Risk</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Priority</th>
                <th className="px-3 py-2">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {data.map((c) => (
                <tr key={c.ref}>
                  <td className="px-3 py-3 font-mono text-[13px]">
                    <Link href={`/console/cases/${c.ref}`} className="underline">
                      {c.ref}
                    </Link>
                  </td>
                  <td className="px-3 py-3">
                    <span className="break-all font-mono text-[13px]">{c.host}</span>
                    {c.brand_name && <div className="text-xs text-zinc-500">Impersonating {c.brand_name}</div>}
                  </td>
                  <td className="px-3 py-3">
                    <VerdictBadge band={c.band} />
                  </td>
                  <td className="px-3 py-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_BADGE[c.status]}`}>
                      {STATUS_LABEL[c.status]}
                    </span>
                  </td>
                  <td className="px-3 py-3 tabular-nums">{c.priority}</td>
                  <td className="px-3 py-3 text-xs text-zinc-500">{formatTime(c.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

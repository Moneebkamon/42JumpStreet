"use client";

import Link from "next/link";
import { useCallback } from "react";

import { VerdictBadge } from "@/components/results/verdict-badge";
import { usePolling } from "@/hooks/use-polling";
import { fetchScans } from "@/lib/api-client";

function when(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

export function ScanHistory() {
  const fetcher = useCallback((signal: AbortSignal) => fetchScans(signal), []);
  const { data, error, loaded } = usePolling(fetcher, 10000);

  if (!loaded) {
    return (
      <p role="status" className="text-sm text-zinc-500">
        Loading your scans...
      </p>
    );
  }
  if (!data) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
        {error ?? "Could not load the history."}
      </p>
    );
  }
  if (data.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-700">
        No scans yet.{" "}
        <Link href="/" className="underline">
          Check a link
        </Link>{" "}
        and it will show up here.
      </p>
    );
  }

  return (
    <ul className="max-h-96 overflow-y-auto divide-y divide-zinc-200 rounded-xl border border-zinc-200 dark:divide-zinc-800 dark:border-zinc-800">
      {data.map((s) => (
        <li key={s.scan_id}>
          <Link
            href={`/scan/${s.scan_id}`}
            className="flex flex-wrap items-center gap-3 px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-900"
          >
            {/* the scanned address is shown as text only, never as a link to it */}
            <span className="min-w-0 flex-1 break-all font-mono text-[13px]">{s.url}</span>
            <span className="flex items-center gap-2">
              <VerdictBadge band={s.band} />
              <span className="tabular-nums text-sm text-zinc-500">{s.score}</span>
            </span>
            <span className="w-full text-xs text-zinc-500 sm:w-auto">
              {when(s.created_at)}
              {s.deep ? " · deep scan" : ""}
              {s.feedback ? ` · marked ${s.feedback}` : ""}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

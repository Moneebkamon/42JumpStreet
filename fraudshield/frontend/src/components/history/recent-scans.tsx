"use client";

import Link from "next/link";
import { useCallback } from "react";

import { VerdictBadge } from "@/components/results/verdict-badge";
import { usePolling } from "@/hooks/use-polling";
import { fetchScans } from "@/lib/api-client";

function age(iso: string): string {
  const secs = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (Number.isNaN(secs)) return iso;
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.floor(secs / 60)} min ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)} h ago`;
  return `${Math.floor(secs / 86400)} d ago`;
}

/** A urlscan-style "recent scans" table for the home page: address, verdict, score, age. */
export function RecentScans() {
  const fetcher = useCallback((signal: AbortSignal) => fetchScans(signal), []);
  const { data, loaded } = usePolling(fetcher, 10000);

  if (!loaded || !data || data.length === 0) return null;

  return (
    <section aria-label="Recent scans" className="mt-12 space-y-3">
      <div className="flex items-baseline justify-between">
        <h2 className="text-sm font-semibold">Recent scans</h2>
        <Link href="/scan" className="text-xs underline">
          See all
        </Link>
      </div>
      <div className="max-h-96 overflow-auto glass rounded-xl border border-zinc-200 dark:border-zinc-800">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
            <tr>
              <th className="px-3 py-2">Address</th>
              <th className="px-3 py-2">Verdict</th>
              <th className="px-3 py-2 text-right">Score</th>
              <th className="px-3 py-2 text-right">Age</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {data.slice(0, 8).map((s) => (
              <tr key={s.scan_id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900">
                <td className="max-w-[16rem] truncate px-3 py-2 font-mono text-[13px] sm:max-w-md">
                  {/* text only, never a link to the scanned address */}
                  <Link href={`/scan/${s.scan_id}`} className="hover:underline" title={s.url}>
                    {s.url}
                  </Link>
                </td>
                <td className="whitespace-nowrap px-3 py-2">
                  <VerdictBadge band={s.band} />
                </td>
                <td className="px-3 py-2 text-right tabular-nums">{s.score}</td>
                <td className="whitespace-nowrap px-3 py-2 text-right text-xs text-zinc-500">{age(s.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

"use client";

import { usePolling } from "@/hooks/use-polling";
import { fetchChecked } from "@/lib/api-client";
import { BAND_META } from "@/lib/format";
import type { CheckedItem } from "@/types/feed";
import type { Band } from "@/types/scan";

function clock(iso: string): string {
  return iso.slice(11, 19);
}

function Result({ item }: { item: CheckedItem }) {
  if (!item.kept) return <span className="text-zinc-400">no brand or scam wording</span>;
  if (item.band === "known") return <span className="text-zinc-500">already scored</span>;
  const meta = BAND_META[item.band as Band];
  if (!meta) return <span className="text-zinc-500">scored</span>;
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${meta.badge}`}>{meta.label}</span>
      <span className="text-zinc-500">{item.score}</span>
      {item.brand_name && <span className="text-zinc-500">(imitates {item.brand_name})</span>}
    </span>
  );
}

/**
 * Every domain the early-detection reader recently looked at, newest first, in a fixed-height box that scrolls on its own.
 * Most are passed over by the cheap name check; only brand-like or scam-worded names are scored.
 */
export function CheckedDomains() {
  const checked = usePolling(fetchChecked, 4000);
  const rows = checked.data ?? [];
  const passed = rows.filter((r) => !r.kept).length;

  return (
    <section className="space-y-2">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Recently checked domains</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          The newest {rows.length.toLocaleString()} domains the reader looked at ({passed.toLocaleString()} passed over by
          the name check, {(rows.length - passed).toLocaleString()} scored). Names are text only; nothing here is opened or
          contacted. Refreshes every few seconds.
        </p>
      </div>
      {checked.error && !checked.data && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {checked.error}
        </p>
      )}
      <div
        className="h-96 overflow-y-auto rounded-xl border border-zinc-200 dark:border-zinc-800"
        tabIndex={0}
        aria-label="Recently checked domains"
      >
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
            <tr>
              <th className="px-3 py-2 font-medium">Time (UTC)</th>
              <th className="px-3 py-2 font-medium">Domain</th>
              <th className="px-3 py-2 font-medium">Result</th>
              <th className="px-3 py-2 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.checked_at}-${r.domain}-${i}`} className="border-t border-zinc-100 dark:border-zinc-900">
                <td className="whitespace-nowrap px-3 py-1.5 tabular-nums text-zinc-500">{clock(r.checked_at)}</td>
                <td className="break-all px-3 py-1.5 font-mono text-[13px]">{r.domain}</td>
                <td className="px-3 py-1.5">
                  <Result item={r} />
                </td>
                <td className="whitespace-nowrap px-3 py-1.5 text-zinc-500">{r.simulated ? "demo sample" : "live stream"}</td>
              </tr>
            ))}
            {checked.loaded && rows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-center text-zinc-500">
                  Nothing checked yet. Start the live reader or replay the demo sample to fill this list.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

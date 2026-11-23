"use client";

import { useEffect, useState } from "react";

import { useLiveFeed } from "@/hooks/use-live-feed";
import type { DiscoveryStats, FeedFilters } from "@/types/feed";

import { FeedFiltersBar } from "./feed-filters";
import { LiveFeedTable } from "./live-feed-table";

function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 px-4 py-3 dark:border-zinc-800">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="text-xs text-zinc-500">{hint}</div>}
    </div>
  );
}

function Kpis({ s }: { s: DiscoveryStats }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Kpi label="Domains checked" value={s.domains_seen.toLocaleString()} />
      <Kpi
        label="Passed the prefilter"
        value={`${(s.pass_through_rate * 100).toFixed(1)}%`}
        hint={`${s.domains_kept} of ${s.domains_seen}`}
      />
      <Kpi label="High risk or worse" value={s.flagged.toLocaleString()} />
      <Kpi label="Avg scoring time" value={`${s.avg_processing_ms} ms`} />
    </div>
  );
}

function ago(iso: string | null, now: number): string {
  if (!iso) return "never";
  const s = Math.max(0, Math.round((now - Date.parse(iso)) / 1000));
  return s < 90 ? `${s} s ago` : s < 5400 ? `${Math.round(s / 60)} min ago` : `${Math.round(s / 3600)} h ago`;
}

/** Is the live certificate reader connected? Its heartbeat is a run recorded every ~20 s while it is up. */
function LiveStatus({ s }: { s: DiscoveryStats }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 5000);
    return () => clearInterval(t);
  }, []);
  const alive = s.last_live_run_at != null && now - Date.parse(s.last_live_run_at) < 90_000;
  return (
    <p className="rounded-xl border border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800">
      <span className={`mr-2 inline-block size-2 rounded-full ${alive ? "bg-emerald-500" : "bg-zinc-400"}`} />
      {alive ? "Live certificate stream connected" : "Live certificate stream is off"}
      {s.last_live_run_at ? ` (last activity ${ago(s.last_live_run_at, now)}, ${s.live_events.toLocaleString()} certificates read)` : " (the reader has not run yet)"}
      {s.last_live_detection_at ? `. Last live detection ${ago(s.last_live_detection_at, now)}.` : "."}
    </p>
  );
}

export function FeedDashboard() {
  // Default hides the "safe" band: those are candidates the prefilter kept but the scorer found little wrong with.
  const [filters, setFilters] = useState<FeedFilters>({ minScore: 30, brand: "" });
  const { feed, stats } = useLiveFeed(filters);

  return (
    <div className="space-y-6">
      {stats.data && <LiveStatus s={stats.data} />}
      {stats.data?.simulated && (
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
          Some rows here come from a simulated demo sample, not real certificates; rows from the live stream appear while the
          reader is on (the list below marks the source of each domain). Scores are estimates from uncalibrated rules, so every
          result is only a suspicion and many are false alarms.
        </p>
      )}

      {stats.data && <Kpis s={stats.data} />}

      <FeedFiltersBar value={filters} brands={stats.data?.top_brands ?? []} onChange={setFilters} />

      {feed.error && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {feed.error} {feed.data ? "Showing the last results." : ""}
        </p>
      )}

      {!feed.loaded ? (
        <p role="status" className="text-sm text-zinc-500">
          Loading the feed...
        </p>
      ) : (
        <LiveFeedTable items={feed.data ?? []} />
      )}
    </div>
  );
}

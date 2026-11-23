"use client";

import { VerdictBadge } from "@/components/results/verdict-badge";
import { usePolling } from "@/hooks/use-polling";
import { fetchQueue } from "@/lib/api-cases";
import { formatTime } from "@/lib/labels";

import { OpenCaseButton } from "./open-case-button";

/** Detections and citizen reports that nobody has opened a case for yet, highest priority first. */
export function TriageQueue() {
  const { data, error, loaded } = usePolling(fetchQueue, 8000);

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Triage queue</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Suspicious domains and citizen reports without a case, ranked by risk and exposure. Reports raise priority but
          never block anything by themselves. Detections come from the live certificate stream while the reader is on, and from a
          simulated demo sample otherwise; many are false alarms until the brand matching is tightened.
        </p>
      </div>
      {!loaded ? (
        <p role="status" className="text-sm text-zinc-500">
          Loading the queue...
        </p>
      ) : !data ? (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {error ?? "Could not load the queue."}
        </p>
      ) : data.length === 0 ? (
        <p className="rounded-xl border border-dashed border-zinc-300 px-4 py-6 text-center text-sm text-zinc-500 dark:border-zinc-700">
          The queue is empty: every flagged domain already has a case.
        </p>
      ) : (
        <div className="max-h-96 overflow-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
              <tr>
                <th className="px-3 py-2">Priority</th>
                <th className="px-3 py-2">Address</th>
                <th className="px-3 py-2">Suspected</th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {data.map((q) => (
                <tr key={`${q.kind}-${q.ref}`} className="align-top">
                  <td className="px-3 py-3 tabular-nums font-semibold">{q.priority}</td>
                  <td className="px-3 py-3">
                    <span className="break-all font-mono text-[13px]">{q.host}</span>
                    {q.brand_name && <div className="text-xs text-zinc-500">Impersonating {q.brand_name}</div>}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2">
                      <VerdictBadge band={q.band} />
                      <span className="tabular-nums text-zinc-500">{q.score}</span>
                    </div>
                  </td>
                  <td className="px-3 py-3 text-xs text-zinc-500">
                    {q.kind === "report" ? `Citizen report ${q.ref}` : "Early detection"}
                    <div>{formatTime(q.when)}</div>
                  </td>
                  <td className="px-3 py-3">
                    <OpenCaseButton source={q.kind} sourceRef={q.ref} label="Open case" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

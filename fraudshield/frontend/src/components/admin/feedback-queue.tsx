"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { VerdictBadge } from "@/components/results/verdict-badge";
import {
  dismissFeedback,
  fetchAllowlist,
  fetchReviewQueue,
  promoteFeedback,
  removeAllowlisted,
  type AllowlistEntry,
  type FlaggedSafe,
} from "@/lib/api-review";
import { formatTime } from "@/lib/labels";
import type { Band } from "@/types/scan";

const INPUT =
  "w-full rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-sm dark:border-zinc-700 dark:bg-zinc-900";

export function FeedbackQueue() {
  const [queue, setQueue] = useState<FlaggedSafe[] | null>(null);
  const [allow, setAllow] = useState<AllowlistEntry[]>([]);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [q, a] = await Promise.all([fetchReviewQueue(), fetchAllowlist()]);
      setQueue(q);
      setAllow(a);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load the queue.");
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchReviewQueue(), fetchAllowlist()])
      .then(([q, a]) => {
        setQueue(q);
        setAllow(a);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the queue."));
  }, []);

  const reasonOf = (key: string) => (reasons[key] ?? "").trim();

  async function act(key: string, fn: (reason: string) => Promise<unknown>, done: string) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn(reasonOf(key));
      setReasons((r) => ({ ...r, [key]: "" }));
      setNotice(done);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Marked safe by a person</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Links we flagged that someone said were safe. Promote only when you have checked it: the whole domain then
          scores low. A known threat-feed hit still wins, and shared-hosting platforms can never be allowlisted.
        </p>
        {queue === null ? (
          error ? null : (
            <p role="status" className="text-sm text-zinc-500">
              Loading...
            </p>
          )
        ) : queue.length === 0 ? (
          <p className="rounded-xl border border-dashed border-zinc-300 px-4 py-6 text-center text-sm text-zinc-500 dark:border-zinc-700">
            Nothing to review.
          </p>
        ) : (
          <ul className="max-h-96 space-y-3 overflow-y-auto pr-1">
            {queue.map((q) => (
              <li key={q.scan_id} className="space-y-2 glass rounded-xl border border-zinc-200 p-3 dark:border-zinc-800">
                <div className="flex flex-wrap items-center gap-2">
                  <VerdictBadge band={q.band as Band} />
                  <span className="text-sm tabular-nums text-zinc-500">score {q.score}</span>
                  <Link href={`/scan/${q.scan_id}`} className="text-xs underline">
                    See the scan
                  </Link>
                  {q.shared_hosting && (
                    <span className="text-xs text-amber-700 dark:text-amber-300">shared hosting: cannot be allowlisted</span>
                  )}
                </div>
                <p className="break-all font-mono text-[13px]">{q.url}</p>
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    aria-label={`Reason for ${q.host}`}
                    placeholder="Reason (required)"
                    value={reasons[q.scan_id] ?? ""}
                    onChange={(e) => setReasons((r) => ({ ...r, [q.scan_id]: e.target.value }))}
                    maxLength={500}
                    className={`${INPUT} min-w-[14rem] flex-1`}
                  />
                  <button
                    type="button"
                    disabled={busy || reasonOf(q.scan_id).length < 3 || q.shared_hosting}
                    onClick={() => act(q.scan_id, (r) => promoteFeedback(q.scan_id, r), `${q.host} is now allowlisted.`)}
                    className="rounded-lg bg-zinc-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
                  >
                    Promote to allowlist
                  </button>
                  <button
                    type="button"
                    disabled={busy || reasonOf(q.scan_id).length < 3}
                    onClick={() => act(q.scan_id, (r) => dismissFeedback(q.scan_id, r), "Dismissed. The domain stays flagged.")}
                    className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm disabled:opacity-50 dark:border-zinc-700"
                  >
                    Dismiss
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Allowlist</h2>
        {allow.length === 0 ? (
          <p className="text-sm text-zinc-500">No domains are allowlisted.</p>
        ) : (
          <ul className="max-h-96 space-y-2 overflow-y-auto pr-1">
            {allow.map((a) => (
              <li key={a.host} className="flex flex-wrap items-center gap-3 text-sm">
                <span className="font-mono text-[13px]">{a.host}</span>
                <span className="text-xs text-zinc-500">
                  {a.added_by} · {formatTime(a.added_at)} · {a.reason}
                </span>
                <input
                  aria-label={`Reason to remove ${a.host}`}
                  placeholder="Reason to remove"
                  value={reasons[`rm-${a.host}`] ?? ""}
                  onChange={(e) => setReasons((r) => ({ ...r, [`rm-${a.host}`]: e.target.value }))}
                  className={`${INPUT} w-48`}
                />
                <button
                  type="button"
                  disabled={busy || reasonOf(`rm-${a.host}`).length < 3}
                  onClick={() => act(`rm-${a.host}`, (r) => removeAllowlisted(a.host, r), `${a.host} was removed from the allowlist.`)}
                  className="text-xs underline disabled:opacity-50"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {notice && (
        <p role="status" className="text-sm text-emerald-700 dark:text-emerald-300">
          {notice}
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}

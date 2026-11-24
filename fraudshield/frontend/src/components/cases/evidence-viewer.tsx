"use client";

import { useState } from "react";

import { freezeEvidence, verifyEvidence, viewEvidence } from "@/lib/api-cases";
import { formatTime } from "@/lib/labels";
import type { EvidenceCheck, EvidenceItem } from "@/types/case";

export function EvidenceViewer({ caseRef, items, onChanged }: { caseRef: string; items: EvidenceItem[]; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checks, setChecks] = useState<Record<number, EvidenceCheck>>({});
  const [open, setOpen] = useState<Record<number, string>>({});

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const freeze = () =>
    run(async () => {
      await freezeEvidence(caseRef);
      setChecks({});
      onChanged();
    });

  return (
    <section className="space-y-3 glass rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Evidence</h2>
        <button
          type="button"
          onClick={freeze}
          disabled={busy}
          className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {items.length ? "Freeze again" : "Freeze evidence"}
        </button>
      </div>
      <p className="text-xs text-zinc-500">
        Freezing stores a copy of the analysis behind this case and a SHA-256 hash of each item, so any later change is
        detectable. Screenshots and page HTML are not captured yet. Every freeze, view and check is written to the audit log.
      </p>
      {items.length === 0 ? (
        <p className="text-sm text-zinc-500">Nothing frozen yet.</p>
      ) : (
        <ul className="max-h-96 overflow-y-auto divide-y divide-zinc-200 dark:divide-zinc-800">
          {items.map((it) => {
            const check = checks[it.id];
            return (
              <li key={it.id} className="space-y-1 py-2 text-sm">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-medium">{it.kind}</span>
                  <span className="text-xs text-zinc-500">
                    {it.size_bytes} bytes · {formatTime(it.captured_at)} · {it.tool_version}
                  </span>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      run(async () => {
                        const r = await verifyEvidence(it.id);
                        setChecks((c) => ({ ...c, [it.id]: r }));
                      })
                    }
                    className="text-xs underline"
                  >
                    Verify hash
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      run(async () => {
                        if (open[it.id] !== undefined) {
                          setOpen((o) => Object.fromEntries(Object.entries(o).filter(([k]) => Number(k) !== it.id)));
                          return;
                        }
                        const r = await viewEvidence(it.id);
                        setOpen((o) => ({ ...o, [it.id]: r.content }));
                      })
                    }
                    className="text-xs underline"
                  >
                    {open[it.id] !== undefined ? "Hide" : "View"}
                  </button>
                  {check && (
                    <span
                      role="status"
                      className={check.ok ? "text-xs font-semibold text-emerald-700 dark:text-emerald-300" : "text-xs font-semibold text-red-700 dark:text-red-300"}
                    >
                      {check.ok ? "Hash matches" : "MISMATCH: this item was changed after it was frozen"}
                    </span>
                  )}
                </div>
                <code className="block break-all text-[11px] text-zinc-500">{it.sha256}</code>
                {open[it.id] !== undefined && (
                  <pre className="max-h-64 overflow-auto rounded-lg bg-zinc-50 p-3 text-[11px] dark:bg-zinc-900">{open[it.id]}</pre>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}

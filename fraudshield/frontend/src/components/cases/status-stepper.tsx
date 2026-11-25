"use client";

import { useState } from "react";

import { changeStatus } from "@/lib/api-cases";
import { STATUS_LABEL, STATUS_PATH } from "@/lib/labels";
import type { CaseDetail, CaseStatus } from "@/types/case";

export function StatusStepper({
  caseRef,
  status,
  allowed,
  onUpdated,
}: {
  caseRef: string;
  status: CaseStatus;
  allowed: CaseStatus[];
  onUpdated: (detail: CaseDetail) => void;
}) {
  const [target, setTarget] = useState<CaseStatus | "">("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chosen = target && allowed.includes(target) ? target : (allowed[0] ?? "");
  const currentIndex = STATUS_PATH.indexOf(status);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!chosen) return;
    setBusy(true);
    setError(null);
    try {
      onUpdated(await changeStatus(caseRef, chosen, reason));
      setReason("");
      setTarget("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change the status.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-3 glass rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
      <h2 className="text-sm font-semibold">Status</h2>
      <ol className="flex flex-wrap gap-2 text-xs" aria-label="Case progress">
        {STATUS_PATH.map((s, i) => (
          <li
            key={s}
            aria-current={s === status ? "step" : undefined}
            className={
              s === status
                ? "rounded-full bg-zinc-900 px-3 py-1 font-semibold text-white dark:bg-zinc-100 dark:text-zinc-900"
                : i < currentIndex
                  ? "rounded-full bg-zinc-200 px-3 py-1 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                  : "rounded-full border border-zinc-300 px-3 py-1 text-zinc-500 dark:border-zinc-700"
            }
          >
            {STATUS_LABEL[s]}
          </li>
        ))}
        {status === "false_positive" && (
          <li aria-current="step" className="rounded-full bg-violet-600 px-3 py-1 font-semibold text-white">
            {STATUS_LABEL.false_positive}
          </li>
        )}
      </ol>

      {allowed.length === 0 ? (
        <p className="text-sm text-zinc-500">This case is final. No further status changes are possible.</p>
      ) : (
        <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
          <label className="space-y-1 text-xs text-zinc-500">
            <span>Move to</span>
            <select
              value={chosen}
              onChange={(e) => setTarget(e.target.value as CaseStatus)}
              className="block rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            >
              {allowed.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABEL[s]}
                </option>
              ))}
            </select>
          </label>
          <label className="min-w-[14rem] flex-1 space-y-1 text-xs text-zinc-500">
            <span>Reason (required, recorded with your name and the time)</span>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={1000}
              required
              className="block w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <button
            type="submit"
            disabled={busy || reason.trim().length < 3}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            {busy ? "Saving..." : "Change status"}
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}

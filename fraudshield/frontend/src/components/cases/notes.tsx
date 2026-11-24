"use client";

import { useState } from "react";

import { addNote } from "@/lib/api-cases";
import { STATUS_LABEL, formatTime } from "@/lib/labels";
import type { CaseDetail, CaseEvent } from "@/types/case";

function describe(e: CaseEvent): string {
  if (e.kind === "status" && e.from_status && e.to_status) {
    return `${STATUS_LABEL[e.from_status]} → ${STATUS_LABEL[e.to_status]}: ${e.text}`;
  }
  return e.text;
}

const KIND_LABEL: Record<CaseEvent["kind"], string> = {
  created: "Opened",
  status: "Status",
  note: "Note",
  evidence: "Evidence",
  takedown_draft: "Draft",
};

/** The case history (every status change, note, evidence freeze and draft) plus a box to add a note. */
export function Notes({ caseRef, events, onUpdated }: { caseRef: string; events: CaseEvent[]; onUpdated: (d: CaseDetail) => void }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      onUpdated(await addNote(caseRef, text));
      setText("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the note.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-3 glass rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
      <h2 className="text-sm font-semibold">History and notes</h2>
      <ol className="max-h-96 space-y-2 overflow-y-auto pr-1">
        {[...events].reverse().map((e) => (
          <li key={e.id} className="text-sm">
            <span className="mr-2 rounded bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
              {KIND_LABEL[e.kind]}
            </span>
            <span className="whitespace-pre-wrap break-words">{describe(e)}</span>
            <span className="block text-xs text-zinc-500">
              {e.actor} · {formatTime(e.at)}
            </span>
          </li>
        ))}
      </ol>
      <form onSubmit={submit} className="flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={2000}
          placeholder="Add a note"
          aria-label="Add a note"
          className="min-w-0 flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        />
        <button
          type="submit"
          disabled={busy || !text.trim()}
          className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium disabled:opacity-50 dark:border-zinc-700"
        >
          Add
        </button>
      </form>
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}

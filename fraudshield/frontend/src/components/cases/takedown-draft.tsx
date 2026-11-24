"use client";

import { useEffect, useState } from "react";

import { createDraft, draftExportUrl, fetchDraft, fetchRecipients } from "@/lib/api-cases";
import { formatTime } from "@/lib/labels";
import type { Draft, DraftSummary } from "@/types/case";

export function TakedownDraft({
  caseRef,
  drafts,
  onChanged,
}: {
  caseRef: string;
  drafts: DraftSummary[];
  onChanged: () => void;
}) {
  const [recipients, setRecipients] = useState<Record<string, string>>({});
  const [recipient, setRecipient] = useState("");
  const [current, setCurrent] = useState<Draft | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchRecipients()
      .then((r) => {
        setRecipients(r);
        setRecipient((cur) => cur || Object.keys(r)[0] || "");
      })
      .catch(() => setError("Could not load the recipient types."));
  }, []);

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

  const create = () =>
    run(async () => {
      setCurrent(await createDraft(caseRef, recipient));
      setCopied(false);
      onChanged();
    });

  async function copy() {
    if (!current) return;
    try {
      await navigator.clipboard.writeText(`Subject: ${current.subject}\n\n${current.body}`);
      setCopied(true);
    } catch {
      setError("Could not copy. Select the text and copy it by hand.");
    }
  }

  return (
    <section className="space-y-3 glass rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
      <h2 className="text-sm font-semibold">Takedown report drafts</h2>
      <p className="text-xs text-zinc-500">
        Manee only drafts and exports text. It never sends anything: an analyst reviews it and sends it by hand.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="space-y-1 text-xs text-zinc-500">
          <span>Recipient</span>
          <select
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            className="block rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
          >
            {Object.entries(recipients).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={create}
          disabled={busy || !recipient}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          Create draft
        </button>
      </div>

      {drafts.length > 0 && (
        <ul className="space-y-1 text-sm">
          {drafts.map((d) => (
            <li key={d.id} className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="text-left underline"
                onClick={() => run(async () => setCurrent(await fetchDraft(d.id)))}
              >
                {recipients[d.recipient_type] ?? d.recipient_type}
              </button>
              <span className="text-xs text-zinc-500">
                {formatTime(d.created_at)}
                {d.exported_at ? " · exported" : ""}
              </span>
            </li>
          ))}
        </ul>
      )}

      {current && (
        <div className="space-y-2">
          <p className="text-sm font-medium">{current.subject}</p>
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-zinc-50 p-3 text-xs dark:bg-zinc-900">
            {current.body}
          </pre>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <button type="button" onClick={copy} className="underline">
              {copied ? "Copied" : "Copy"}
            </button>
            <a href={draftExportUrl(current.id)} download className="underline" onClick={() => setTimeout(onChanged, 800)}>
              Download as text file
            </a>
          </div>
        </div>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700 dark:text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}

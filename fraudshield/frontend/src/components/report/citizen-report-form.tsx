"use client";

import { useState } from "react";

import { VerdictBadge } from "@/components/results/verdict-badge";
import { submitReport } from "@/lib/api-cases";
import type { ReportReceipt } from "@/types/case";

const FIELD =
  "block w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900";

export function CitizenReportForm() {
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [contact, setContact] = useState("");
  const [website, setWebsite] = useState(""); // honeypot: hidden from people, bots tend to fill it
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<ReportReceipt | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setReceipt(await submitReport({ url, note, contact, website }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send your report.");
    } finally {
      setBusy(false);
    }
  }

  if (receipt) {
    return (
      <section aria-live="polite" className="space-y-4 glass rounded-2xl border border-zinc-200 p-6 dark:border-zinc-800">
        <h2 className="text-lg font-semibold">Thank you. Your report was received.</h2>
        <p className="text-sm">
          Reference number: <strong className="font-mono">{receipt.ref}</strong>
        </p>
        <div className="flex items-center gap-2">
          <VerdictBadge band={receipt.band} />
          <span className="text-sm tabular-nums text-zinc-500">score {receipt.score}</span>
        </div>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{receipt.advice}</p>
        <p className="text-xs text-zinc-500">
          Your report helps analysts prioritise. It does not block a site by itself, and nobody opened the link you sent.
        </p>
        <button
          type="button"
          onClick={() => {
            setReceipt(null);
            setUrl("");
            setNote("");
            setContact("");
          }}
          className="text-sm underline"
        >
          Report another link
        </button>
      </section>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">The suspicious link</span>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          maxLength={2048}
          placeholder="https://..."
          className={FIELD}
        />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">What happened? (optional)</span>
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          maxLength={1000}
          rows={3}
          placeholder="For example: I got this link in an SMS saying my parcel was held."
          className={FIELD}
        />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">How can we reach you? (optional)</span>
        <input value={contact} onChange={(e) => setContact(e.target.value)} maxLength={200} className={FIELD} />
      </label>

      {/* honeypot: off-screen, not focusable, ignored by assistive tech */}
      <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
        <label>
          Leave this field empty
          <input tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
        </label>
      </div>

      {error && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={busy || !url.trim()}
        className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
      >
        {busy ? "Sending..." : "Send report"}
      </button>
      <p className="text-xs text-zinc-500">
        We check the link from its text and domain only. We do not open the page. Please do not enter personal
        details on the suspicious site.
      </p>
    </form>
  );
}

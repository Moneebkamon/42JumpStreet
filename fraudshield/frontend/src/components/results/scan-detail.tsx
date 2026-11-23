"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { useMe } from "@/hooks/use-me";
import { OpenCaseButton } from "@/components/cases/open-case-button";
import { NotFoundError, fetchScan, sendVerdict } from "@/lib/api-client";
import type { StoredScan, Verdict } from "@/types/scan";

import { ScanResultCard } from "./scan-result";

type State =
  | { status: "loading" }
  | { status: "done"; scan: StoredScan }
  | { status: "error"; message: string };

/** Unwraps the route params (a promise in this Next version) and shows that scan. */
export function ScanDetailRoute({ params }: { params: Promise<{ scanId: string }> }) {
  const { scanId } = use(params);
  return <ScanDetail scanId={scanId} />;
}

function ScanDetail({ scanId }: { scanId: string }) {
  const { me } = useMe();
  const [state, setState] = useState<State>({ status: "loading" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchScan(scanId, ctrl.signal)
      .then((scan) => setState({ status: "done", scan }))
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setState({
          status: "error",
          message: err instanceof NotFoundError ? err.message : "Could not load this scan. Please try again.",
        });
      });
    return () => ctrl.abort();
  }, [scanId]);

  async function answer(label: Verdict) {
    setSaving(true);
    setSaveError(null);
    try {
      await sendVerdict(scanId, label);
      setState((s) => (s.status === "done" ? { status: "done", scan: { ...s.scan, feedback: label } } : s));
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Could not save your answer.");
    } finally {
      setSaving(false);
    }
  }

  if (state.status === "loading") {
    return (
      <p role="status" className="text-center text-sm text-zinc-500">
        Loading the scan...
      </p>
    );
  }
  if (state.status === "error") {
    return (
      <div className="space-y-3 text-center">
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {state.message}
        </p>
        <Link href="/scan" className="text-sm underline">
          Back to your scans
        </Link>
      </div>
    );
  }

  const { scan } = state;
  return (
    <div className="space-y-5">
      <ScanResultCard result={scan} />

      <section className="space-y-2 rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">Help us improve</h2>
        {scan.feedback ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Thanks. You marked this link as <strong>{scan.feedback}</strong>. You can change your answer.
          </p>
        ) : (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">Do you know whether this link is a scam?</p>
        )}
        <div className="flex gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={() => answer("scam")}
            className="rounded-lg border border-red-300 px-3 py-1.5 text-sm text-red-800 hover:bg-red-50 disabled:opacity-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950"
          >
            It is a scam
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => answer("safe")}
            className="rounded-lg border border-emerald-300 px-3 py-1.5 text-sm text-emerald-800 hover:bg-emerald-50 disabled:opacity-50 dark:border-emerald-800 dark:text-emerald-300 dark:hover:bg-emerald-950"
          >
            It is safe
          </button>
        </div>
        {saveError && (
          <p role="alert" className="text-sm text-red-700 dark:text-red-300">
            {saveError}
          </p>
        )}
      </section>

      {me && (
      <section className="space-y-2 rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">For analysts</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Open a case to review this link, freeze evidence and prepare a takedown report.
        </p>
        <OpenCaseButton source="scan" sourceRef={scan.scan_id} />
      </section>
      )}

      <p className="text-center text-xs text-zinc-500">
        Scanned {scan.created_at.replace("T", " ").replace("Z", " UTC")} ·{" "}
        <Link href="/scan" className="underline">
          all scans
        </Link>
      </p>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConflictError, openCase } from "@/lib/api-cases";

/** Opens a case from a scan, a discovered domain or a citizen report, then goes to the case page. */
export function OpenCaseButton({
  source,
  sourceRef,
  label = "Open a case",
}: {
  source: "scan" | "detection" | "report";
  sourceRef: string;
  label?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existing, setExisting] = useState<string | null>(null);

  async function go() {
    setBusy(true);
    setError(null);
    try {
      const created = await openCase(source, sourceRef);
      router.push(`/console/cases/${created.ref}`);
    } catch (err) {
      if (err instanceof ConflictError && err.ref) setExisting(err.ref);
      setError(err instanceof Error ? err.message : "Could not open the case.");
      setBusy(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={go}
        disabled={busy}
        className="rounded-lg border border-zinc-300 px-3 py-1 text-xs font-medium hover:bg-zinc-50 disabled:opacity-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
      >
        {busy ? "Opening..." : label}
      </button>
      {error && (
        <span role="alert" className="text-xs text-red-700 dark:text-red-300">
          {error}{" "}
          {existing && (
            <Link href={`/console/cases/${existing}`} className="underline">
              Open {existing}
            </Link>
          )}
        </span>
      )}
    </span>
  );
}

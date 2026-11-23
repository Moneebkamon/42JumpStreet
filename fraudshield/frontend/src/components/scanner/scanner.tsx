"use client";

import Link from "next/link";

import { useScan } from "@/hooks/use-scan";

import { ScanResultCard } from "../results/scan-result";
import { UrlInput } from "./url-input";

export function Scanner() {
  const { state, scan } = useScan();

  return (
    <div className="space-y-6">
      <UrlInput onSubmit={scan} busy={state.status === "loading"} />

      {state.status === "loading" && (
        <p role="status" className="text-center text-sm text-zinc-500">
          {state.deep
            ? "Opening the page in a safe browser and checking the domain. This can take several seconds..."
            : "Checking the link and looking up the domain..."}
        </p>
      )}

      {state.status === "error" && (
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {state.message}
        </p>
      )}

      {state.status === "done" && (
        <>
          <ScanResultCard result={state.result} />
          <p className="text-center text-sm">
            <Link href={`/scan/${state.result.scan_id}`} className="underline">
              Open the saved result
            </Link>{" "}
            to tell us whether it was a scam.
          </p>
        </>
      )}
    </div>
  );
}

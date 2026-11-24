"use client";

import Link from "next/link";
import { use, useCallback, useEffect, useState } from "react";

import { ApiError, NotFoundError } from "@/lib/api-client";
import { fetchCase } from "@/lib/api-cases";
import type { CaseDetail } from "@/types/case";

import { CaseHeader } from "./case-header";
import { EvidenceViewer } from "./evidence-viewer";
import { Notes } from "./notes";
import { StatusStepper } from "./status-stepper";
import { TakedownDraft } from "./takedown-draft";

type State = { status: "loading" } | { status: "done"; detail: CaseDetail } | { status: "error"; message: string };

/** Unwraps the route params (a promise in this Next version) and shows that case. */
export function CaseRoute({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = use(params);
  return <CaseView caseRef={caseId} />;
}

function CaseView({ caseRef }: { caseRef: string }) {
  const [state, setState] = useState<State>({ status: "loading" });

  const reload = useCallback(() => {
    fetchCase(caseRef)
      .then((detail) => setState({ status: "done", detail }))
      .catch((err) =>
        setState({
          status: "error",
          message:
            err instanceof NotFoundError || (err instanceof ApiError && /not found/i.test(err.message))
              ? "We could not find that case."
              : "Could not load this case. Please try again.",
        }),
      );
  }, [caseRef]);

  useEffect(() => {
    reload();
  }, [reload]);

  if (state.status === "loading") {
    return (
      <p role="status" className="text-sm text-zinc-500">
        Loading the case...
      </p>
    );
  }
  if (state.status === "error") {
    return (
      <div className="space-y-3">
        <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
          {state.message}
        </p>
        <Link href="/console/cases" className="text-sm underline">
          Back to cases
        </Link>
      </div>
    );
  }

  const d = state.detail;
  const setDetail = (detail: CaseDetail) => setState({ status: "done", detail });
  return (
    <div className="space-y-5">
      <CaseHeader c={d} />
      <StatusStepper caseRef={d.ref} status={d.status} allowed={d.allowed_next} onUpdated={setDetail} />
      <section className="space-y-2 glass rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">Why it was flagged</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm">
          {d.result.reasons.length === 0 ? <li>No specific rule fired.</li> : d.result.reasons.map((r) => <li key={r.rule}>{r.reason}</li>)}
        </ul>
      </section>
      <EvidenceViewer caseRef={d.ref} items={d.evidence} onChanged={reload} />
      <TakedownDraft caseRef={d.ref} drafts={d.takedown_drafts} onChanged={reload} />
      <Notes caseRef={d.ref} events={d.events} onUpdated={setDetail} />
    </div>
  );
}

import Link from "next/link";

import { RequireStaff } from "@/components/auth/require-staff";
import { CheckedDomains } from "@/components/feed/checked-domains";
import { FeedDashboard } from "@/components/feed/feed-dashboard";
import { TriageQueue } from "@/components/cases/triage-queue";

export default function ConsolePage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-10 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Analyst console</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Triage what was found, open cases, freeze evidence and prepare reports for human review.{" "}
          <Link href="/console/cases" className="underline">
            See all cases
          </Link>
          .
        </p>
      </header>
      <RequireStaff>
      <TriageQueue />
      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Early detection feed</h2>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Newly issued certificate domains that look like UAE brands or scam patterns, scored automatically before
            anyone reported them.
          </p>
        </div>
        <FeedDashboard />
      </section>
      <CheckedDomains />
      </RequireStaff>
    </main>
  );
}

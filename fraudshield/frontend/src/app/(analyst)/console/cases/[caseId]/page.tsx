import Link from "next/link";
import { Suspense } from "react";

import { RequireStaff } from "@/components/auth/require-staff";
import { CaseRoute } from "@/components/cases/case-view";

export default function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 space-y-4 px-4 py-10">
      <Link href="/console/cases" className="text-sm underline">
        All cases
      </Link>
      {/* params are only known at request time, so they are read inside Suspense (Cache Components) */}
      <Suspense fallback={<p className="text-sm text-zinc-500">Loading the case...</p>}>
        <RequireStaff>
          <CaseRoute params={params} />
        </RequireStaff>
      </Suspense>
    </main>
  );
}

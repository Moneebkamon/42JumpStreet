import { Suspense } from "react";

import { ScanDetailRoute } from "@/components/results/scan-detail";

export default function ScanDetailPage({ params }: { params: Promise<{ scanId: string }> }) {
  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-10">
      {/* params are only known at request time, so they are read inside Suspense (Cache Components) */}
      <Suspense fallback={<p className="text-center text-sm text-zinc-500">Loading the scan...</p>}>
        <ScanDetailRoute params={params} />
      </Suspense>
    </main>
  );
}

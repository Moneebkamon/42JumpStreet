import Link from "next/link";

import { ScanHistory } from "@/components/history/scan-history";

export default function ScanHistoryPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Your scans</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Every link checked here is saved.{" "}
          <Link href="/" className="underline">
            Check another link
          </Link>
          .
        </p>
      </header>
      <ScanHistory />
    </main>
  );
}

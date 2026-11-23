import Link from "next/link";

import { RecentScans } from "@/components/history/recent-scans";
import { Scanner } from "@/components/scanner/scanner";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-12 sm:py-20">
      <header className="mb-8 space-y-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">FraudShield</h1>
        <p className="text-zinc-600 dark:text-zinc-400">
          Got a suspicious link from a message, a search result or a map listing? Paste it to check it before you
          open it.
        </p>
      </header>
      <Scanner />
      <RecentScans />
      <nav className="mt-10 flex justify-center gap-6 text-sm text-zinc-600 dark:text-zinc-400">
        <Link href="/report" className="underline">
          Report a scam
        </Link>
        <Link href="/login" className="underline">
          Staff sign-in
        </Link>
      </nav>
    </main>
  );
}

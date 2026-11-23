import Link from "next/link";

/** Stand-in for pages that belong to a later stage, so every route in the app opens cleanly. */
export function ComingSoon({ title, note }: { title: string; note: string }) {
  return (
    <main className="mx-auto w-full max-w-xl flex-1 space-y-3 px-4 py-16 text-center">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{note}</p>
      <p className="text-sm">
        <Link href="/" className="underline">
          Back to the scanner
        </Link>
      </p>
    </main>
  );
}

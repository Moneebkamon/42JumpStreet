import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
      <h1 className="text-xl font-semibold">Page not found</h1>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">That page doesn&apos;t exist.</p>
      <Link href="/" className="mt-6 inline-block rounded-xl bg-foreground px-5 py-2.5 font-medium text-background">
        Check a link
      </Link>
    </main>
  );
}

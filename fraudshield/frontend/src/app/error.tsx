"use client"; // Error boundaries must be Client Components

import { useEffect } from "react";

export default function Error({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="mx-auto w-full max-w-xl flex-1 px-4 py-20 text-center">
      <h1 className="text-xl font-semibold">Something went wrong</h1>
      <p className="mt-2 text-zinc-600 dark:text-zinc-400">The page could not be shown. Please try again.</p>
      <button onClick={() => retry()} className="mt-6 rounded-xl bg-foreground px-5 py-2.5 font-medium text-background">
        Try again
      </button>
    </main>
  );
}

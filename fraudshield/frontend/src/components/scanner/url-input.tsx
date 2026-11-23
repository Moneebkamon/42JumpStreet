"use client";

import { useState } from "react";

import { useMe } from "@/hooks/use-me";

export function UrlInput({
  onSubmit,
  busy,
}: {
  onSubmit: (url: string, deep: boolean) => void;
  busy: boolean;
}) {
  const [value, setValue] = useState("");
  const [wantDeep, setDeep] = useState(false);
  const { me } = useMe();
  const deep = wantDeep && !!me; // the safe-browser option is for signed-in staff only

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const url = value.trim();
        if (url) onSubmit(url, deep);
      }}
      className="space-y-3"
    >
      <div className="flex flex-col gap-2 sm:flex-row">
        <label htmlFor="url" className="sr-only">
          Link to check
        </label>
        <input
          id="url"
          type="text"
          inputMode="url"
          autoComplete="off"
          spellCheck={false}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Paste a link, for example https://example.com/login"
          className="min-w-0 flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-3 text-base outline-none focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-300"
        />
        <button
          type="submit"
          disabled={busy || !value.trim()}
          className="rounded-xl bg-foreground px-6 py-3 font-medium text-background transition-opacity disabled:opacity-40"
        >
          {busy ? "Checking..." : "Check link"}
        </button>
      </div>

      {me ? (
        <label className="flex cursor-pointer items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <input
            type="checkbox"
            checked={deep}
            onChange={(e) => setDeep(e.target.checked)}
            className="mt-0.5 size-4"
          />
          <span>
            <span className="font-medium text-foreground">Also open the page in a safe browser (staff only).</span>{" "}
            Catches fake login forms; nothing is typed or submitted. <strong>Demo build: use it on the staged test pages
            only, not on real scam sites.</strong>
          </span>
        </label>
      ) : (
        <p className="text-xs text-zinc-500">
          This check reads the link and its domain. It never opens the page. Opening pages is limited to signed-in staff.
        </p>
      )}
    </form>
  );
}

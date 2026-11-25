"use client";

import { useState } from "react";

import { useMe } from "@/hooks/use-me";
import { isStaffRole } from "@/lib/api-auth";

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
  const staff = !!me && isStaffRole(me.role);
  const deep = wantDeep && staff; // the safe-browser option is for staff accounts only

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
          className="min-w-0 flex-1 rounded-xl border border-zinc-300 bg-white px-4 dark:border-zinc-700 dark:bg-zinc-950/70 py-3 font-mono text-[15px] outline-none transition placeholder:font-sans placeholder:text-zinc-500 focus:border-brand/70 focus:ring-4 focus:ring-brand/15"
        />
        <button
          type="submit"
          disabled={busy || !value.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand to-brand-2 px-6 py-3 font-semibold text-brand-ink shadow-[0_8px_30px_-10px_var(--brand)] transition hover:-translate-y-px hover:shadow-[0_12px_34px_-8px_var(--brand)] disabled:translate-y-0 disabled:opacity-40 disabled:shadow-none"
        >
          {busy && <span className="size-4 animate-spin rounded-full border-2 border-brand-ink/30 border-t-brand-ink" />}
          {busy ? "Scanning..." : "Scan link"}
        </button>
      </div>

      {staff ? (
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
          This check reads the link and its domain. It never opens the page. Deep search (opening the page in a safe browser) is available to staff accounts.
        </p>
      )}
    </form>
  );
}

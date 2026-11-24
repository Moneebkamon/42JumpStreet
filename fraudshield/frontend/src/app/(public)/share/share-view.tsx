"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ScanResultCard } from "@/components/results/scan-result";
import { Notice } from "@/components/ui/kit";
import { ApiError, scanUrl } from "@/lib/api-client";
import { extractLinks } from "@/lib/extract-links";
import type { ScanResult } from "@/types/scan";

type Item = { url: string; result?: ScanResult; error?: string };

/** "Share to Manee": the phone's Share menu opens this page with the message text, and we check every link in it. */
export function ShareView() {
  const params = useSearchParams();
  const shared = [params.get("title"), params.get("text"), params.get("url")].filter(Boolean).join("\n");
  const [items, setItems] = useState<Item[] | null>(null);

  useEffect(() => {
    const links = extractLinks(shared);
    if (links.length === 0) {
      setItems([]);
      return;
    }
    const ctrl = new AbortController();
    setItems(links.map((url) => ({ url })));
    links.forEach((url, i) => {
      scanUrl(url, { signal: ctrl.signal })
        .then((result) => setItems((cur) => cur && cur.map((it, j) => (j === i ? { ...it, result } : it))))
        .catch((e: unknown) => {
          if (e instanceof DOMException && e.name === "AbortError") return;
          const error = e instanceof ApiError ? e.message : "Could not check this link.";
          setItems((cur) => cur && cur.map((it, j) => (j === i ? { ...it, error } : it)));
        });
    });
    return () => ctrl.abort();
  }, [shared]);

  return (
    <div className="mx-auto w-full max-w-2xl space-y-5 px-4 py-8">
      <h1 className="text-xl font-semibold">Manee check</h1>
      {items === null ? null : items.length === 0 ? (
        <Notice tone="info">
          {shared ? "No link found in what you shared." : "Share a message or a link to Manee from any app and it is checked here."}
        </Notice>
      ) : (
        items.map((it) => (
          <section key={it.url} className="space-y-2">
            <p className="break-all font-mono text-xs text-muted" dir="ltr">
              {it.url}
            </p>
            {it.result ? (
              <ScanResultCard result={it.result} />
            ) : it.error ? (
              <Notice tone="error">{it.error}</Notice>
            ) : (
              <p role="status" className="text-sm text-muted">
                Checking...
              </p>
            )}
          </section>
        ))
      )}
      <p className="text-xs text-muted">Manee checks the link text only and never opens the page on your phone.</p>
    </div>
  );
}

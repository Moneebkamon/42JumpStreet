"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { Badge, BandBadge, Button, Card, Notice, PageHeader, cn } from "@/components/ui/kit";
import { useLoad } from "@/hooks/use-load";
import { usePrefs } from "@/i18n/provider";
import type { MessageKey } from "@/i18n/config";
import { clearHistory, fetchHistory } from "@/lib/api-me";
import { ageLabel } from "@/lib/time";

const SOURCES: { value: string; key: MessageKey }[] = [
  { value: "", key: "hist.all" },
  { value: "manual", key: "hist.manual" },
  { value: "extension", key: "hist.extension" },
  { value: "message", key: "hist.message" },
];

export default function HistoryPage() {
  const { t } = usePrefs();
  const [source, setSource] = useState("");
  const fetcher = useCallback((s: AbortSignal) => fetchHistory(source, s), [source]);
  const { data, error, loading, reload } = useLoad(fetcher);
  const [clearError, setClearError] = useState<string | null>(null);

  async function clear() {
    if (!window.confirm(t("hist.clear") + "?")) return;
    setClearError(null);
    try {
      await clearHistory();
      reload();
    } catch (e) {
      setClearError(e instanceof Error ? e.message : "Could not clear.");
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("hist.title")}
        subtitle={t("hist.subtitle")}
        action={<Button variant="danger" onClick={clear}>{t("hist.clear")}</Button>}
      />
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Source">
        {SOURCES.map((s) => (
          <button
            key={s.value}
            role="tab"
            aria-selected={source === s.value}
            onClick={() => setSource(s.value)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              source === s.value ? "border-brand bg-brand/15 text-brand" : "border-line text-muted hover:text-foreground",
            )}
          >
            {t(s.key)}
          </button>
        ))}
      </div>
      {clearError && <Notice tone="error">{clearError}</Notice>}
      {error && <Notice tone="error">{error.message}</Notice>}
      <Card className="overflow-hidden p-0">
        {loading ? (
          <p className="p-5 text-sm text-muted">{t("common.loading")}</p>
        ) : !data || data.length === 0 ? (
          <p className="p-5 text-sm text-muted">{t("hist.empty")}</p>
        ) : (
          <div className="max-h-[32rem] overflow-auto">
            <table className="w-full text-start text-sm">
              <thead className="sticky top-0 bg-zinc-100 text-xs uppercase tracking-wide text-muted dark:bg-zinc-900">
                <tr>
                  <th className="px-4 py-2 text-start">URL</th>
                  <th className="px-4 py-2 text-start">Verdict</th>
                  <th className="px-4 py-2 text-end">Score</th>
                  <th className="px-4 py-2 text-start">Source</th>
                  <th className="px-4 py-2 text-end">When</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.map((h, i) => (
                  <tr key={`${h.url}-${h.created_at}-${i}`}>
                    <td className="max-w-xs truncate px-4 py-2 font-mono text-xs" title={h.url}>
                      {h.scan_id ? <Link href={`/scan/${h.scan_id}`} className="underline">{h.url}</Link> : h.url}
                    </td>
                    <td className="px-4 py-2"><BandBadge band={h.band} /></td>
                    <td className="px-4 py-2 text-end tabular-nums">{h.score}</td>
                    <td className="px-4 py-2"><Badge>{h.source}</Badge></td>
                    <td className="px-4 py-2 text-end text-xs text-muted">{ageLabel(h.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

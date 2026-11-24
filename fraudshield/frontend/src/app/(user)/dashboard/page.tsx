"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge, BandBadge, ButtonLink, Card, CardTitle, Notice, PageHeader, StatTile, Switch } from "@/components/ui/kit";
import { useLoad } from "@/hooks/use-load";
import { usePrefs } from "@/i18n/provider";
import { fetchHistory, fetchSummary, putSettings } from "@/lib/api-me";
import { ageLabel } from "@/lib/time";

async function loadAll(signal: AbortSignal) {
  // TODO(DELETE LATER - privacy): message alerts (fetchAlerts) are switched off
  const [summary, history] = await Promise.all([fetchSummary(signal), fetchHistory("", signal)]);
  return { summary, history: history.slice(0, 6) };
}

export default function DashboardPage() {
  const { t } = usePrefs();
  const { data, error, loading, setData, pauseRefresh } = useLoad(loadAll, 5000);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  if (loading) return <p className="text-sm text-muted">{t("common.loading")}</p>;
  if (error || !data) return <Notice tone="error">{error?.message ?? "Could not load your dashboard."}</Notice>;

  const { summary, history } = data;
  const enabled = summary.settings.extension_enabled;

  async function toggleExtension(next: boolean) {
    setBusy(true);
    setSaveError(null);
    pauseRefresh(true); // a refresh that started before this click must not put the old value back
    try {
      const settings = await putSettings({ extension_enabled: next });
      setData((cur) => (cur ? { ...cur, summary: { ...cur.summary, settings } } : cur));
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : "Could not save.");
    }
    pauseRefresh(false);
    setBusy(false);
  }

  return (
    <div className="space-y-6">
      <PageHeader title={`${t("dash.hello")}, ${summary.username}`} subtitle={t("dash.title")} />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label={t("dash.links")} value={summary.scans + summary.visits} />
        <StatTile label={t("dash.risky")} value={summary.risky_scans + summary.risky_visits} tone={summary.risky_scans + summary.risky_visits > 0 ? "bad" : undefined} />
        <StatTile label={t("dash.blocked")} value={summary.blocked} tone={summary.blocked > 0 ? "bad" : undefined} />
        <StatTile label={t("dash.contacts")} value={summary.contacts} />
      </div>

      <Card>
        <CardTitle hint={<Badge tone={enabled ? "safe" : "neutral"}>{enabled ? t("common.on") : t("common.off")}</Badge>}>
          {t("dash.ext.title")}
        </CardTitle>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="max-w-lg text-sm text-muted">{enabled ? t("dash.ext.on") : t("dash.ext.off")}</p>
          <div className="flex items-center gap-3">
            {summary.devices === 0 && <ButtonLink href="/devices" variant="secondary">{t("dash.ext.link")}</ButtonLink>}
            <Switch checked={enabled} onChange={toggleExtension} label={t("dash.ext.title")} disabled={busy} />
          </div>
        </div>
        {saveError && <div className="mt-3"><Notice tone="error">{saveError}</Notice></div>}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardTitle hint={<Link href="/history" className="underline">{t("nav.history")}</Link>}>{t("dash.recent")}</CardTitle>
          {history.length === 0 ? (
            <p className="text-sm text-muted">{t("dash.none")}</p>
          ) : (
            <ul className="divide-y divide-line">
              {history.map((h, i) => (
                <li key={`${h.url}-${i}`} className="flex items-center gap-3 py-2 text-sm">
                  <span className="min-w-0 flex-1 truncate font-mono text-xs" title={h.url}>{h.url}</span>
                  <BandBadge band={h.band} />
                  <span className="w-14 text-end text-xs text-muted">{ageLabel(h.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* TODO(DELETE LATER - privacy): message alerts card is switched off
        <Card>
          <CardTitle hint={<Link href="/watchlist" className="underline">{t("nav.watchlist")}</Link>}>{t("dash.alerts")}</CardTitle>
          {alerts.length === 0 ? (
            <div className="space-y-3">
              <p className="text-sm text-muted">{t("watch.alerts.empty")}</p>
              {summary.contacts === 0 && <ButtonLink href="/watchlist" variant="secondary">{t("watch.add")}</ButtonLink>}
            </div>
          ) : (
            <ul className="divide-y divide-line">
              {alerts.map((a) => (
                <li key={a.id} className="space-y-1 py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge tone={a.action === "blocked" ? "bad" : a.action === "monitor" ? "warn" : "safe"}>{t(`watch.${a.action}`)}</Badge>
                    <span className="text-xs uppercase text-muted">{a.channel}</span>
                    <span className="ms-auto text-xs text-muted">{ageLabel(a.created_at)}</span>
                  </div>
                  <div className="truncate font-mono text-xs" title={a.links[0]?.url}>{a.links[0]?.url}</div>
                </li>
              ))}
            </ul>
          )}
        </Card>
        */}
      </div>
    </div>
  );
}

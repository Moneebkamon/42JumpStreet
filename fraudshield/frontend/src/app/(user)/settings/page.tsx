"use client";

import { useState } from "react";

import { LanguageSwitch } from "@/components/layout/language-switch";
import { Button, Card, CardTitle, Input, Notice, PageHeader, Switch } from "@/components/ui/kit";
import { useLoad } from "@/hooks/use-load";
import { usePrefs } from "@/i18n/provider";
import { changePassword } from "@/lib/api-auth";
import { fetchSummary, putSettings } from "@/lib/api-me";

export default function SettingsPage() {
  const { t } = usePrefs();
  const { data, error, setData } = useLoad(fetchSummary);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [msg, setMsg] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  async function toggleAlerts(v: boolean) {
    try {
      const settings = await putSettings({ alerts_enabled: v });
      setData((cur) => (cur ? { ...cur, settings } : cur));
    } catch (e) {
      setMsg({ tone: "error", text: e instanceof Error ? e.message : "Could not save." });
    }
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      await changePassword(current, next);
      setCurrent("");
      setNext("");
      setMsg({ tone: "ok", text: "Password changed." });
    } catch (err) {
      setMsg({ tone: "error", text: err instanceof Error ? err.message : "Could not change the password." });
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t("set.title")} />
      {error && <Notice tone="error">{error.message}</Notice>}
      {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}

      <Card>
        <CardTitle>{t("nav.watchlist")}</CardTitle>
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm">{t("set.alerts")}</span>
          <Switch checked={!!data?.settings.alerts_enabled} onChange={toggleAlerts} label={t("set.alerts")} disabled={!data} />
        </div>
      </Card>

      <Card>
        <CardTitle>{t("set.appearance")}</CardTitle>
        <div className="flex items-center gap-3">
          <LanguageSwitch />
        </div>
      </Card>

      <Card>
        <CardTitle>{t("set.password")}</CardTitle>
        <form onSubmit={savePassword} className="max-w-sm space-y-3">
          <label className="block space-y-1 text-sm">
            <span>{t("set.current")}</span>
            <Input type="password" value={current} onChange={(e) => setCurrent(e.target.value)} autoComplete="current-password" required />
          </label>
          <label className="block space-y-1 text-sm">
            <span>{t("set.new")}</span>
            <Input type="password" value={next} onChange={(e) => setNext(e.target.value)} autoComplete="new-password" minLength={8} required />
          </label>
          <Button type="submit" disabled={!current || next.length < 8}>{t("set.save")}</Button>
        </form>
      </Card>
    </div>
  );
}

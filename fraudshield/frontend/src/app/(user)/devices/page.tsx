"use client";

import { useState } from "react";

import { Badge, Button, Card, CardTitle, Notice, PageHeader, Switch } from "@/components/ui/kit";
import { useLoad } from "@/hooks/use-load";
import { usePrefs } from "@/i18n/provider";
import { extensionInstalled, linkExtension } from "@/lib/extension-bridge";
import { createDevice, fetchDevices, fetchSummary, putSettings, removeDevice } from "@/lib/api-me";
import { ageLabel } from "@/lib/time";

async function loadAll(signal: AbortSignal) {
  const [devices, summary] = await Promise.all([fetchDevices(signal), fetchSummary(signal)]);
  return { devices, enabled: summary.settings.extension_enabled };
}

export default function DevicesPage() {
  const { t } = usePrefs();
  const { data, error, loading, reload, setData } = useLoad(loadAll);
  const [token, setToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  async function create() {
    setMsg(null);
    setCopied(false);
    try {
      const r = await createDevice("Chrome");
      setToken(r.token);
      reload();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not create a code.");
    }
  }

  async function toggle(next: boolean) {
    setMsg(null);
    try {
      await putSettings({ extension_enabled: next });
      setData((cur) => (cur ? { ...cur, enabled: next } : cur));
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not save.");
    }
  }

  async function remove(id: number) {
    try {
      await removeDevice(id);
      reload();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not remove.");
    }
  }

  async function copy() {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
    } catch {
      setMsg("Copy failed. Select the code and copy it by hand.");
    }
  }

  /** One click: make a code and hand it straight to the installed extension. Falls back to showing the code. */
  async function connect() {
    setMsg(null);
    setNote(null);
    setConnecting(true);
    try {
      if (!(await extensionInstalled())) {
        setNote(t("dev.absent"));
        await create();
        return;
      }
      const r = await createDevice("Chrome");
      reload();
      if (await linkExtension(r.token)) {
        setToken(null);
        setNote(t("dev.connected"));
      } else {
        setToken(r.token);
        setCopied(false);
        setNote(t("dev.connectfail"));
      }
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Could not connect.");
    } finally {
      setConnecting(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t("dev.title")} subtitle={t("dev.subtitle")} />
      {error && <Notice tone="error">{error.message}</Notice>}
      {msg && <Notice tone="error">{msg}</Notice>}

      <Card>
        <CardTitle hint={<Badge tone={data?.enabled ? "safe" : "neutral"}>{data?.enabled ? t("common.on") : t("common.off")}</Badge>}>
          {t("dash.ext.title")}
        </CardTitle>
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm text-muted">{data?.enabled ? t("dash.ext.on") : t("dash.ext.off")}</p>
          <Switch checked={!!data?.enabled} onChange={toggle} label={t("dash.ext.title")} disabled={!data} />
        </div>
      </Card>

      <Card>
        <CardTitle>{t("dev.connect")}</CardTitle>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <Button onClick={connect} disabled={connecting}>{connecting ? t("dev.connecting") : t("dev.connect")}</Button>
          {note && <span className="text-sm text-muted">{note}</span>}
        </div>
        <p className="mb-2 text-xs font-medium text-muted">{t("dev.or")}</p>
        <p className="mb-4 text-sm text-muted">{t("dev.steps")}</p>
        {token ? (
          <div className="space-y-2">
            <div className="text-xs text-muted">{t("dev.token")}</div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <code className="min-w-0 flex-1 break-all rounded-lg border border-line bg-zinc-100 px-3 py-2 text-xs dark:bg-zinc-900" dir="ltr">{token}</code>
              <Button variant="secondary" onClick={copy}>{copied ? "Copied" : "Copy"}</Button>
            </div>
          </div>
        ) : (
          <Button onClick={create}>{t("dev.create")}</Button>
        )}
      </Card>

      <Card>
        <CardTitle>{t("dev.linked")}</CardTitle>
        {loading ? (
          <p className="text-sm text-muted">{t("common.loading")}</p>
        ) : !data || data.devices.length === 0 ? (
          <p className="text-sm text-muted">{t("dash.none")}</p>
        ) : (
          <ul className="divide-y divide-line">
            {data.devices.map((d) => (
              <li key={d.id} className="flex items-center gap-3 py-2 text-sm">
                <span className="flex-1">{d.label}</span>
                <span className="text-xs text-muted">{d.last_seen ? ageLabel(d.last_seen) : t("dev.never")}</span>
                <Button variant="danger" onClick={() => remove(d.id)} className="px-2 py-1 text-xs">{t("dev.remove")}</Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

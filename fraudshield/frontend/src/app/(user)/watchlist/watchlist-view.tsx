"use client";

import { useState } from "react";

import { Badge, Button, Card, CardTitle, FIELD, Input, Notice, PageHeader, cn } from "@/components/ui/kit";
import { WhatsAppCard } from "@/components/user/whatsapp-card";
import { useLoad } from "@/hooks/use-load";
import { usePrefs } from "@/i18n/provider";
import type { MessageKey } from "@/i18n/config";
import { addContact, fetchAlerts, fetchContacts, removeContact, type ContactKind } from "@/lib/api-me";
import { ageLabel } from "@/lib/time";

async function loadAll(signal: AbortSignal) {
  const [contacts, alerts] = await Promise.all([fetchContacts(signal), fetchAlerts(signal)]);
  return { contacts, alerts };
}

export function WatchlistView() {
  const { t } = usePrefs();
  const { data, error, loading, reload } = useLoad(loadAll, 5000);
  const [kind, setKind] = useState<ContactKind>("phone");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setFormError(null);
    try {
      await addContact(kind, value.trim());
      setValue("");
      reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not add.");
    }
    setBusy(false);
  }

  async function remove(id: number) {
    try {
      await removeContact(id);
      reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not remove.");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t("watch.title")} subtitle={t("watch.subtitle")} />

      <WhatsAppCard onLinked={reload} />

      <Card>
        <form onSubmit={add} className="flex flex-col gap-2 sm:flex-row">
          <select value={kind} onChange={(e) => setKind(e.target.value as ContactKind)} aria-label="Type" className={cn(FIELD, "sm:w-44")}>
            <option value="phone">{t("watch.kind.phone")}</option>
            <option value="whatsapp">{t("watch.kind.whatsapp")}</option>
            <option value="email">{t("watch.kind.email")}</option>
          </select>
          <Input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={kind === "email" ? "name@example.com" : "+971 50 123 4567"}
            aria-label={t("watch.value")}
            dir="ltr"
            required
          />
          <Button type="submit" disabled={busy || !value.trim()}>{t("watch.add")}</Button>
        </form>
        {formError && <div className="mt-3"><Notice tone="error">{formError}</Notice></div>}

        {loading ? (
          <p className="mt-4 text-sm text-muted">{t("common.loading")}</p>
        ) : !data || data.contacts.length === 0 ? (
          <p className="mt-4 text-sm text-muted">{t("watch.empty")}</p>
        ) : (
          <ul className="mt-4 divide-y divide-line">
            {data.contacts.map((c) => (
              <li key={c.id} className="flex items-center gap-3 py-2 text-sm">
                <Badge tone="info">{t(`watch.kind.${c.kind}` as MessageKey)}</Badge>
                <span className="flex-1 font-mono text-xs" dir="ltr">{c.value}</span>
                <Button variant="ghost" onClick={() => remove(c.id)} className="px-2 py-1 text-xs">Remove</Button>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {error && <Notice tone="error">{error.message}</Notice>}

      <Card>
        <CardTitle>{t("watch.alerts")}</CardTitle>
        {!data || data.alerts.length === 0 ? (
          <p className="text-sm text-muted">{t("watch.alerts.empty")}</p>
        ) : (
          <ul className="divide-y divide-line">
            {data.alerts.map((a) => (
              <li key={a.id} className="space-y-1.5 py-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={a.action === "blocked" ? "bad" : a.action === "monitor" ? "warn" : "safe"}>{t(`watch.${a.action}` as MessageKey)}</Badge>
                  <span className="text-xs uppercase text-muted">{a.channel}</span>
                  <span className="text-xs text-muted" dir="ltr">from {a.sender}</span>
                  {a.emailed && <Badge tone="info">{t("watch.emailed")}</Badge>}
                  <span className="ms-auto text-xs text-muted">{ageLabel(a.created_at)}</span>
                </div>
                {a.links.map((l) => (
                  <div key={l.url} className="font-mono text-xs" dir="ltr">
                    <span className="break-all">{l.url}</span>{" "}
                    <span className="text-muted">({l.score}/100{l.reasons[0] ? `: ${l.reasons[0]}` : ""})</span>
                  </div>
                ))}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

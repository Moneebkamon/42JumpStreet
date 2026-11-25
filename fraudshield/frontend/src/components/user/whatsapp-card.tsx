"use client";

import { useEffect, useState } from "react";

import { Badge, Button, Card, CardTitle, Input, Notice } from "@/components/ui/kit";
import { usePrefs } from "@/i18n/provider";
import { connectWhatsApp, disconnectWhatsApp, fetchWhatsApp, refreshWhatsApp, type WhatsAppState } from "@/lib/api-me";

/** Link a WhatsApp number from the site: enter the number, scan the QR code, done. */
export function WhatsAppCard({ onLinked }: { onLinked?: () => void }) {
  const { t } = usePrefs();
  const [state, setState] = useState<WhatsAppState | null>(null);
  const [number, setNumber] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pending = state?.status === "connecting";

  useEffect(() => {
    let live = true;
    fetchWhatsApp()
      .then((s) => live && setState(s))
      .catch((e: unknown) => live && setError(e instanceof Error ? e.message : "Could not load."));
    return () => {
      live = false;
    };
  }, []);

  // While waiting for the scan, poll the status. The QR is only returned by connect/refresh, so keep the one we have.
  useEffect(() => {
    if (!pending) return;
    const id = setInterval(() => {
      fetchWhatsApp()
        .then((s) => {
          const done = s.status === "open";
          setState((cur) => ({ ...s, qr: done ? null : (cur?.qr ?? null), pairing_code: done ? null : (cur?.pairing_code ?? null) }));
          if (done) onLinked?.();
        })
        .catch(() => undefined);
    }, 3000);
    return () => clearInterval(id);
  }, [pending, onLinked]);

  // A QR code is only valid for a short while, so fetch a fresh one every 20 seconds until it is scanned.
  useEffect(() => {
    if (!pending) return;
    const id = setInterval(() => {
      refreshWhatsApp()
        .then((s) => setState((cur) => (cur?.status === "open" || s.status === "open" ? { ...s, qr: null, pairing_code: null } : s)))
        .catch(() => undefined);
    }, 20000);
    return () => clearInterval(id);
  }, [pending]);

  async function run(fn: () => Promise<WhatsAppState>) {
    setBusy(true);
    setError(null);
    try {
      setState(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    }
    setBusy(false);
  }

  return (
    <Card>
      <CardTitle hint={state?.linked ? <Badge tone="safe">{t("wa.connected")}</Badge> : undefined}>{t("wa.title")}</CardTitle>
      <p className="mb-4 text-sm text-muted">{t("wa.subtitle")}</p>
      {error && (
        <div className="mb-3">
          <Notice tone="error">{error}</Notice>
        </div>
      )}

      {state && !state.available ? (
        <Notice tone="info">{t("wa.unavailable")}</Notice>
      ) : state?.linked ? (
        <div className="flex items-center justify-between gap-3">
          <span className="font-mono text-sm" dir="ltr">
            {state.number}
          </span>
          <Button variant="danger" disabled={busy} onClick={() => run(disconnectWhatsApp)}>
            {t("wa.disconnect")}
          </Button>
        </div>
      ) : pending ? (
        <div className="space-y-3">
          {state?.qr && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={state.qr} alt="WhatsApp QR code" className="size-56 rounded-xl border border-line bg-white p-2" />
          )}
          <p className="text-sm text-muted">{t("wa.scan")}</p>
          {state?.pairing_code && (
            <p className="text-sm text-muted">
              {t("wa.pairing")}{" "}
              <code className="rounded bg-zinc-200 px-2 py-0.5 font-mono text-foreground dark:bg-zinc-800">{state.pairing_code}</code>
            </p>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs text-muted">{t("wa.waiting")}</span>
            <Button variant="secondary" disabled={busy} onClick={() => run(refreshWhatsApp)}>
              {t("wa.refresh")}
            </Button>
            <Button variant="ghost" disabled={busy} onClick={() => run(disconnectWhatsApp)}>
              {t("wa.disconnect")}
            </Button>
          </div>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(() => connectWhatsApp(number.trim()));
          }}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input value={number} onChange={(e) => setNumber(e.target.value)} placeholder="+971 50 123 4567" aria-label={t("wa.number")} dir="ltr" required />
          <Button type="submit" disabled={busy || !number.trim() || !state}>
            {t("wa.connect")}
          </Button>
        </form>
      )}
      <p className="mt-4 text-xs text-muted">{t("wa.privacy")}</p>
    </Card>
  );
}

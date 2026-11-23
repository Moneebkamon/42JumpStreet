import { CHECK_LABELS, BAND_META, describeDays } from "@/lib/format";
import type { ScanPage, ScanResult } from "@/types/scan";

import { ReasonsList } from "./reasons-list";
import { RiskGauge } from "./risk-gauge";
import { VerdictBadge } from "./verdict-badge";

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-zinc-50 px-3 py-2 dark:bg-zinc-900">
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="break-words text-sm font-medium">{value}</dd>
    </div>
  );
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname || url;
  } catch {
    return url; // a malformed address must never break the result card
  }
}

function PageSection({ page }: { page: ScanPage }) {
  const { phones, wallets, handles } = page.contacts;
  const hops = Math.max(0, page.redirect_chain.length - 1);
  const facts: { label: string; value: string }[] = [
    { label: "Page title", value: page.title || "(none)" },
    { label: "Redirects", value: hops === 0 ? "None" : `${hops} (ends on ${hostOf(page.final_url)})` },
  ];
  if (phones.length) facts.push({ label: "Phone numbers", value: phones.join(", ") });
  if (wallets.length) facts.push({ label: "Crypto wallets", value: wallets.join(", ") });
  if (handles.length) facts.push({ label: "Chat handles", value: handles.join(", ") });

  return (
    <div>
      <h2 className="mb-2 text-sm font-semibold">What the page showed</h2>
      <dl className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {facts.map((x) => (
          <Fact key={x.label} {...x} />
        ))}
      </dl>
      {page.blocked_hosts.length > 0 && (
        <p className="mt-2 text-xs text-zinc-500">
          The safe browser refused to contact internal addresses the page asked for: {page.blocked_hosts.join(", ")}.
        </p>
      )}
    </div>
  );
}

export function ScanResultCard({ result }: { result: ScanResult }) {
  const f = result.features;
  const facts: { label: string; value: string }[] = [];
  if ("domain_age_days" in f) {
    const age = f.domain_age_days;
    facts.push({ label: "Domain age", value: typeof age === "number" ? describeDays(age) : "Unknown" });
  }
  if ("tls_cert_age_days" in f) {
    const age = f.tls_cert_age_days;
    facts.push({ label: "Certificate issued", value: typeof age === "number" ? `${describeDays(age)} ago` : "Unknown" });
  }

  const checks = result.analyzers_ok.map((a) => CHECK_LABELS[a] ?? a);
  const sandboxFailed = result.analyzers_failed.includes("sandbox");

  return (
    <section
      aria-live="polite"
      className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"
    >
      <p className="break-all text-xs text-zinc-500">{result.url}</p>

      <div className="space-y-3 text-center">
        <RiskGauge score={result.score} band={result.band} />
        <VerdictBadge band={result.band} />
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{BAND_META[result.band].summary}</p>
      </div>

      {result.explanation && (
        <p className="rounded-xl bg-zinc-50 px-4 py-3 text-sm leading-relaxed dark:bg-zinc-900">{result.explanation}</p>
      )}

      {sandboxFailed && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
          The page could not be opened safely (it may be offline, blocked or too slow), so only the link and
          domain were checked.
        </p>
      )}

      <div>
        <h2 className="mb-2 text-sm font-semibold">Why</h2>
        <ReasonsList reasons={result.reasons} />
      </div>

      {result.page && <PageSection page={result.page} />}

      {facts.length > 0 && (
        <dl className="grid grid-cols-2 gap-2">
          {facts.map((x) => (
            <Fact key={x.label} {...x} />
          ))}
        </dl>
      )}

      <p className="border-t border-zinc-100 pt-3 text-xs text-zinc-500 dark:border-zinc-900">
        Checked: {checks.join(", ")}.{" "}
        {result.page
          ? "The page was opened in an isolated browser; nothing was typed or submitted. This is an automated assessment, not a final verdict."
          : "The page itself was not opened. Tick the safe-browser option for a deeper check. This is an early warning, not a final verdict."}
      </p>
    </section>
  );
}

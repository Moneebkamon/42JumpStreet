import { OpenCaseButton } from "@/components/cases/open-case-button";
import { VerdictBadge } from "@/components/results/verdict-badge";
import type { FeedItem } from "@/types/feed";

function time(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toISOString().slice(0, 16).replace("T", " ") + " UTC";
}

export function LiveFeedTable({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-zinc-300 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-700">
        No domains match these filters yet.
      </p>
    );
  }

  return (
    <div className="max-h-96 overflow-auto glass rounded-xl border border-zinc-200 dark:border-zinc-800">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
          <tr>
            <th className="px-3 py-2">Domain</th>
            <th className="px-3 py-2">Suspected</th>
            <th className="px-3 py-2">Why</th>
            <th className="px-3 py-2">Certificate issued</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {items.map((it) => (
            <tr key={it.domain} className="align-top">
              <td className="px-3 py-3">
                {/* shown as text on purpose: never a link to a suspected scam site */}
                <span className="break-all font-mono text-[13px]">{it.domain}</span>
                {it.brand_name && <div className="text-xs text-zinc-500">Impersonating {it.brand_name}</div>}
              </td>
              <td className="px-3 py-3">
                <div className="flex items-center gap-2">
                  <VerdictBadge band={it.band} />
                  <span className="tabular-nums text-zinc-500">{it.score}</span>
                </div>
              </td>
              <td className="px-3 py-3 text-zinc-700 dark:text-zinc-300">
                <ul className="list-disc space-y-0.5 pl-4">
                  {it.reasons.slice(0, 3).map((r) => (
                    <li key={r.rule}>{r.reason}</li>
                  ))}
                </ul>
              </td>
              <td className="px-3 py-3 text-xs text-zinc-500">{time(it.issued_at)}</td>
              <td className="px-3 py-3">
                <OpenCaseButton source="detection" sourceRef={it.domain} label="Open case" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

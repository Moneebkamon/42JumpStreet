import { VerdictBadge } from "@/components/results/verdict-badge";
import { STATUS_BADGE, STATUS_LABEL, formatTime } from "@/lib/labels";
import type { CaseSummary } from "@/types/case";

export function CaseHeader({ c }: { c: CaseSummary }) {
  return (
    <header className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm text-zinc-500">{c.ref}</span>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_BADGE[c.status]}`}>
          {STATUS_LABEL[c.status]}
        </span>
        <VerdictBadge band={c.band} />
        <span className="text-sm tabular-nums text-zinc-500">score {c.score}</span>
        <span className="text-sm tabular-nums text-zinc-500">priority {c.priority}</span>
      </div>
      <h1 className="text-2xl font-semibold tracking-tight">{c.title}</h1>
      {/* the address is text on purpose: never a link to a suspected scam site */}
      <p className="break-all font-mono text-[13px]">{c.url}</p>
      <p className="text-xs text-zinc-500">
        {c.brand_name ? `Possible impersonation of ${c.brand_name} · ` : ""}
        opened from {c.source} by {c.created_by} · {formatTime(c.created_at)} · updated {formatTime(c.updated_at)}
      </p>
      <p className="text-xs text-zinc-500">
        Wording stays &quot;suspected&quot; until an analyst confirms the case. Nothing here is sent to anyone.
      </p>
    </header>
  );
}

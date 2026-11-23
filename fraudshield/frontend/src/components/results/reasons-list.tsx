import type { Reason } from "@/types/scan";

export function ReasonsList({ reasons }: { reasons: Reason[] }) {
  if (reasons.length === 0) {
    return <p className="text-sm text-zinc-600 dark:text-zinc-400">No warning signs were found.</p>;
  }
  return (
    <ul className="space-y-2">
      {reasons.map((r) => (
        <li key={r.rule} className="flex items-start justify-between gap-3 text-sm">
          <span>{r.reason}</span>
          {r.points > 0 && (
            <span className="shrink-0 rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              +{r.points}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}

"use client";

import { usePolling } from "@/hooks/use-polling";
import { fetchAudit } from "@/lib/api-cases";
import { formatTime } from "@/lib/labels";

export function AuditLog() {
  const { data, error, loaded } = usePolling(fetchAudit, 10000);

  if (!loaded) {
    return (
      <p role="status" className="text-sm text-zinc-500">
        Loading the audit log...
      </p>
    );
  }
  if (!data) {
    return (
      <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
        {error ?? "Could not load the audit log."}
      </p>
    );
  }
  if (data.length === 0) {
    return <p className="text-sm text-zinc-500">Nothing has been recorded yet.</p>;
  }
  return (
    <div className="max-h-96 overflow-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
      <table className="w-full min-w-[36rem] text-left text-sm">
        <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
          <tr>
            <th className="px-3 py-2">When</th>
            <th className="px-3 py-2">Who</th>
            <th className="px-3 py-2">Action</th>
            <th className="px-3 py-2">On</th>
            <th className="px-3 py-2">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
          {data.map((a) => (
            <tr key={a.id} className="align-top">
              <td className="px-3 py-2 text-xs text-zinc-500">{formatTime(a.at)}</td>
              <td className="px-3 py-2">{a.actor}</td>
              <td className="px-3 py-2 font-mono text-[13px]">{a.action}</td>
              <td className="px-3 py-2 font-mono text-[13px]">
                {a.object_type} {a.object_id}
              </td>
              <td className="px-3 py-2 text-xs text-zinc-600 dark:text-zinc-400">{a.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

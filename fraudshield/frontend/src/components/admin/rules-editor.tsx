"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchSettings,
  previewSettings,
  resetSettings,
  saveCutoffs,
  saveRule,
  type PreviewResult,
  type SettingsView,
} from "@/lib/api-admin";
import { formatTime } from "@/lib/labels";

const BAND_LABEL: Record<string, string> = {
  safe: "Looks safe",
  suspicious: "Suspicious",
  high_risk: "High risk",
  likely_fraud: "Likely fraud",
};
const INPUT =
  "w-20 rounded-lg border border-zinc-300 bg-white px-2 py-1 text-sm tabular-nums dark:border-zinc-700 dark:bg-zinc-900";

export function RulesEditor() {
  const [view, setView] = useState<SettingsView | null>(null);
  const [points, setPoints] = useState<Record<string, string>>({});
  const [cut, setCut] = useState<string[]>(["", "", ""]);
  const [reason, setReason] = useState("");
  const [preview, setPreview] = useState<PreviewResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const adopt = useCallback((v: SettingsView) => {
    setView(v);
    setPoints(Object.fromEntries(v.rules.map((r) => [r.name, String(r.current)])));
    setCut(v.cutoffs.current.map(String));
    setPreview(null);
  }, []);

  useEffect(() => {
    fetchSettings()
      .then(adopt)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load the settings."));
  }, [adopt]);

  if (!view) {
    return error ? (
      <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 dark:bg-red-950 dark:text-red-300">
        {error}
      </p>
    ) : (
      <p role="status" className="text-sm text-zinc-500">
        Loading the settings...
      </p>
    );
  }

  const changedRules = view.rules.filter((r) => Number(points[r.name]) !== r.current);
  const cutNums = cut.map(Number);
  const cutChanged = cutNums.some((n, i) => n !== view.cutoffs.current[i]);
  const dirty = changedRules.length > 0 || cutChanged;
  const proposedRules = Object.fromEntries(changedRules.map((r) => [r.name, Number(points[r.name])]));

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const doPreview = () =>
    run(async () => setPreview(await previewSettings(proposedRules, cutChanged ? cutNums : null)));

  const doSave = () =>
    run(async () => {
      let latest = view!;
      for (const r of changedRules) latest = await saveRule(r.name, Number(points[r.name]), reason);
      if (cutChanged) latest = await saveCutoffs(cutNums, reason);
      adopt(latest);
      setReason("");
      setNotice("Saved. New scans use these numbers right away.");
    });

  const doReset = () =>
    run(async () => {
      adopt(await resetSettings(reason));
      setReason("");
      setNotice("Everything is back to the default numbers.");
    });

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Rule points</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Points a rule adds when it fires (0 switches it off, at most {view.max_points}). Scores are capped at 100.
        </p>
        <div className="max-h-96 overflow-auto rounded-xl border border-zinc-200 dark:border-zinc-800">
          <table className="w-full min-w-[30rem] text-left text-sm">
            <thead className="sticky top-0 z-10 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-900">
              <tr>
                <th className="px-3 py-2">Rule</th>
                <th className="px-3 py-2">Default</th>
                <th className="px-3 py-2">Points</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
              {view.rules.map((r) => {
                const edited = Number(points[r.name]) !== r.current;
                return (
                  <tr key={r.name} className={r.changed || edited ? "bg-amber-50/60 dark:bg-amber-950/20" : ""}>
                    <td className="px-3 py-2 font-mono text-[13px]">
                      {r.name}
                      {!r.implemented && <span className="ml-2 text-xs text-zinc-500">(not built yet)</span>}
                    </td>
                    <td className="px-3 py-2 tabular-nums text-zinc-500">{r.default}</td>
                    <td className="px-3 py-2">
                      <input
                        aria-label={`Points for ${r.name}`}
                        type="number"
                        min={0}
                        max={view.max_points}
                        value={points[r.name]}
                        onChange={(e) => setPoints((p) => ({ ...p, [r.name]: e.target.value }))}
                        className={INPUT}
                      />
                      {r.changed && !edited && <span className="ml-2 text-xs text-amber-700 dark:text-amber-300">changed</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Risk band cutoffs</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          The lowest score of each band. Today: safe 0-{view.bands[0].max}, suspicious {view.bands[1].min}-{view.bands[1].max},
          high risk {view.bands[2].min}-{view.bands[2].max}, likely fraud {view.bands[3].min}-100.
        </p>
        <div className="flex flex-wrap gap-4">
          {["suspicious", "high_risk", "likely_fraud"].map((b, i) => (
            <label key={b} className="space-y-1 text-xs text-zinc-500">
              <span>{BAND_LABEL[b]} from</span>
              <input
                type="number"
                min={1}
                max={100}
                value={cut[i]}
                onChange={(e) => setCut((c) => c.map((v, j) => (j === i ? e.target.value : v)))}
                className={`${INPUT} block`}
              />
            </label>
          ))}
        </div>
      </section>

      <section className="space-y-3 rounded-2xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">Check, then save</h2>
        <div className="flex flex-wrap items-end gap-3">
          <button
            type="button"
            onClick={doPreview}
            disabled={busy || !dirty}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium disabled:opacity-50 dark:border-zinc-700"
          >
            Preview the effect on recent scans
          </button>
          <label className="min-w-[14rem] flex-1 space-y-1 text-xs text-zinc-500">
            <span>Reason (required, recorded with your name)</span>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={500}
              className="block w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
          <button
            type="button"
            onClick={doSave}
            disabled={busy || !dirty || reason.trim().length < 3}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
          >
            Save
          </button>
          <button
            type="button"
            onClick={doReset}
            disabled={busy || reason.trim().length < 3}
            className="rounded-lg border border-zinc-300 px-4 py-2 text-sm disabled:opacity-50 dark:border-zinc-700"
          >
            Reset all to defaults
          </button>
        </div>
        {preview && (
          <div className="space-y-2 rounded-lg bg-zinc-50 p-3 text-sm dark:bg-zinc-900" role="status">
            <p>
              Checked {preview.scans_checked} stored scan(s): <strong>{preview.changed_count}</strong> would change.
            </p>
            <p className="text-xs text-zinc-500">
              {Object.keys(BAND_LABEL)
                .map((b) => `${BAND_LABEL[b]}: ${preview.before[b] ?? 0} → ${preview.after[b] ?? 0}`)
                .join(" · ")}
            </p>
            {preview.changed.length > 0 && (
              <ul className="max-h-72 space-y-1 overflow-y-auto pr-1 text-xs">
                {preview.changed.map((c) => (
                  <li key={c.scan_id} className="break-all font-mono">
                    {c.url}: {c.old_score} ({BAND_LABEL[c.old_band]}) → {c.new_score} ({BAND_LABEL[c.new_band]})
                  </li>
                ))}
              </ul>
            )}
            <p className="text-xs text-zinc-500">
              Scores are re-calculated from the stored page checks. Nothing is saved until you press Save.
            </p>
          </div>
        )}
        {notice && (
          <p role="status" className="text-sm text-emerald-700 dark:text-emerald-300">
            {notice}
          </p>
        )}
        {error && (
          <p role="alert" className="text-sm text-red-700 dark:text-red-300">
            {error}
          </p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold tracking-tight">Change history</h2>
        {view.history.length === 0 ? (
          <p className="text-sm text-zinc-500">No changes yet: all numbers are the defaults.</p>
        ) : (
          <ul className="max-h-72 space-y-2 overflow-y-auto pr-1 text-sm">
            {view.history.map((h) => (
              <li key={h.id}>
                <span className="font-mono text-[13px]">{h.key}</span>: {h.old_value ?? "default"} → {h.new_value ?? "default"}
                <span className="block text-xs text-zinc-500">
                  {h.actor} · {formatTime(h.at)} · {h.reason}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

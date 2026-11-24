"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Load something once on mount, with reload(). `fetcher` must be stable (useCallback or a module function).
 * `refreshMs` re-fetches quietly in the background (no loading state, paused while the tab is hidden).
 */
export function useLoad<T>(fetcher: (signal: AbortSignal) => Promise<T>, refreshMs?: number) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  const held = useRef(false); // true while the page saves something: background refreshes must not overwrite it
  const inflight = useRef<AbortController | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    let live = true;
    fetcher(ctrl.signal)
      .then((d) => {
        if (live) {
          setData(d);
          setError(null);
          setLoading(false);
        }
      })
      .catch((e: unknown) => {
        if (e instanceof DOMException && e.name === "AbortError") return;
        if (live) {
          setError(e instanceof Error ? e : new Error("Failed"));
          setLoading(false);
        }
      });
    return () => {
      live = false;
      ctrl.abort();
    };
  }, [fetcher, tick]);

  useEffect(() => {
    if (!refreshMs) return;
    const id = setInterval(() => {
      if (document.hidden || held.current) return;
      inflight.current?.abort();
      const ctrl = new AbortController();
      inflight.current = ctrl;
      fetcher(ctrl.signal)
        .then((d) => {
          if (!held.current && !ctrl.signal.aborted) setData(d);
        })
        .catch(() => undefined); // keep showing the last good data
    }, refreshMs);
    return () => {
      clearInterval(id);
      inflight.current?.abort();
    };
  }, [fetcher, refreshMs]);

  /** Call pauseRefresh(true) before saving a change and pauseRefresh(false) after, so a slow refresh cannot undo it. */
  const pauseRefresh = useCallback((on: boolean) => {
    held.current = on;
    if (on) inflight.current?.abort();
  }, []);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data, error, loading, reload, setData, pauseRefresh };
}

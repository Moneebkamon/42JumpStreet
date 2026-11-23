"use client";

import { useEffect, useRef, useState } from "react";

export type Polled<T> = { data: T | null; error: string | null; loaded: boolean };

/**
 * Call `fetcher` now and then every `intervalMs`. Keeps the last good data if a refresh fails.
 * `fetcher` should be stable per set of inputs (wrap it in useCallback); a new one restarts polling.
 */
export function usePolling<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  intervalMs: number,
): Polled<T> {
  const [state, setState] = useState<Polled<T>>({ data: null, error: null, loaded: false });
  const latest = useRef(fetcher);

  useEffect(() => {
    latest.current = fetcher;
  }, [fetcher]);

  useEffect(() => {
    let alive = true;
    let ctrl = new AbortController();

    async function tick() {
      ctrl.abort();
      ctrl = new AbortController();
      try {
        const data = await latest.current(ctrl.signal);
        if (alive) setState({ data, error: null, loaded: true });
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (alive) {
          setState((s) => ({
            data: s.data,
            error: err instanceof Error ? err.message : "Something went wrong.",
            loaded: true,
          }));
        }
      }
    }

    void tick();
    const id = setInterval(() => void tick(), intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
      ctrl.abort();
    };
  }, [fetcher, intervalMs]);

  return state;
}

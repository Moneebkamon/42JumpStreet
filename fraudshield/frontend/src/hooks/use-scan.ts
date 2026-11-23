"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, scanUrl } from "@/lib/api-client";
import type { ScanResult } from "@/types/scan";

type ScanState =
  | { status: "idle" }
  | { status: "loading"; url: string; deep: boolean }
  | { status: "done"; result: ScanResult }
  | { status: "error"; message: string };

export function useScan() {
  const [state, setState] = useState<ScanState>({ status: "idle" });
  const controller = useRef<AbortController | null>(null);

  // Cancel an in-flight request if the component goes away.
  useEffect(() => () => controller.current?.abort(), []);

  const scan = useCallback(async (url: string, deep: boolean) => {
    controller.current?.abort(); // a newer scan replaces the old one
    const ctrl = new AbortController();
    controller.current = ctrl;
    setState({ status: "loading", url, deep });
    try {
      const result = await scanUrl(url, { deep, signal: ctrl.signal });
      setState({ status: "done", result });
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setState({
        status: "error",
        message: err instanceof ApiError ? err.message : "Something went wrong. Please try again.",
      });
    }
  }, []);

  return { state, scan };
}

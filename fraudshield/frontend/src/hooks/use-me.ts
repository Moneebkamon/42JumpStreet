"use client";

import { useEffect, useState } from "react";

import { fetchMe, type Me } from "@/lib/api-auth";

export type MeState = { loaded: boolean; me: Me | null };

/** Who is signed in. Re-checks when the page asks (after login or logout, via the "fs-auth" event). */
export function useMe(): MeState {
  const [state, setState] = useState<MeState>({ loaded: false, me: null });

  useEffect(() => {
    const ctrl = new AbortController();
    const load = () =>
      fetchMe(ctrl.signal)
        .then((me) => setState({ loaded: true, me }))
        .catch((err) => {
          if (!(err instanceof DOMException && err.name === "AbortError")) setState({ loaded: true, me: null });
        });
    load();
    window.addEventListener("fs-auth", load);
    return () => {
      ctrl.abort();
      window.removeEventListener("fs-auth", load);
    };
  }, []);

  return state;
}

export function announceAuthChange() {
  window.dispatchEvent(new Event("fs-auth"));
}

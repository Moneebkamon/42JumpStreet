"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, useSyncExternalStore } from "react";

import { DICTIONARIES, DIR, LANG_KEY, THEME_KEY, type Lang, type MessageKey } from "./config";

type Theme = "dark" | "light";
type Prefs = {
  lang: Lang;
  theme: Theme;
  t: (key: MessageKey) => string;
  setLang: (l: Lang) => void;
  toggleTheme: () => void;
};

const Ctx = createContext<Prefs | null>(null);

// The source of truth is the <html> element (lang + data-theme), set before first paint by the script in layout.tsx.
function subscribe(onChange: () => void): () => void {
  const obs = new MutationObserver(onChange);
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ["lang", "data-theme"] });
  return () => obs.disconnect();
}
const getLang = (): Lang => (document.documentElement.lang === "ar" ? "ar" : "en");
const getTheme = (): Theme => (document.documentElement.dataset.theme === "light" ? "light" : "dark");

/** Language (en/ar with RTL) and theme (dark/light). */
export function PreferencesProvider({ children }: { children: React.ReactNode }) {
  const domLang = useSyncExternalStore(subscribe, getLang, () => "en" as Lang);
  const domTheme = useSyncExternalStore(subscribe, getTheme, () => "dark" as Theme);
  // Until after hydration, render what the server rendered (en/dark); then switch to the saved preference.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const lang: Lang = mounted ? domLang : "en";
  const theme: Theme = mounted ? domTheme : "dark";

  const setLang = useCallback((l: Lang) => {
    document.documentElement.lang = l;
    document.documentElement.dir = DIR[l];
    try {
      localStorage.setItem(LANG_KEY, l);
    } catch {}
  }, []);

  const toggleTheme = useCallback(() => {
    const next: Theme = getTheme() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {}
  }, []);

  const value = useMemo<Prefs>(
    () => ({ lang, theme, setLang, toggleTheme, t: (key) => DICTIONARIES[lang][key] ?? DICTIONARIES.en[key] ?? key }),
    [lang, theme, setLang, toggleTheme],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function usePrefs(): Prefs {
  const v = useContext(Ctx);
  if (!v) throw new Error("usePrefs needs <PreferencesProvider>");
  return v;
}

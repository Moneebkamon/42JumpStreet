"use client";

import { usePrefs } from "@/i18n/provider";

/** EN / AR switch (Arabic flips the page to right-to-left). */
export function LanguageSwitch() {
  const { lang, setLang } = usePrefs();
  return (
    <button
      type="button"
      suppressHydrationWarning
      onClick={() => setLang(lang === "en" ? "ar" : "en")}
      aria-label={lang === "en" ? "Switch to Arabic" : "Switch to English"}
      className="rounded-lg border border-line px-2.5 py-1.5 text-xs font-medium text-muted transition-colors hover:text-foreground"
    >
      {lang === "en" ? "العربية" : "English"}
    </button>
  );
}

export function ThemeToggle() {
  const { theme, toggleTheme } = usePrefs();
  return (
    <button
      type="button"
      suppressHydrationWarning
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      className="grid size-8 place-items-center rounded-lg border border-line text-muted transition-colors hover:text-foreground"
    >
      {theme === "dark" ? (
        <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="size-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
        </svg>
      )}
    </button>
  );
}

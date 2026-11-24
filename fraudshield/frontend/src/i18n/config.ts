import ar from "./messages/ar.json";
import en from "./messages/en.json";

export const LANGS = ["en", "ar"] as const;
export type Lang = (typeof LANGS)[number];
export type MessageKey = keyof typeof en;

export const DICTIONARIES: Record<Lang, Record<string, string>> = { en, ar };
export const DIR: Record<Lang, "ltr" | "rtl"> = { en: "ltr", ar: "rtl" };
export const LANG_KEY = "fs-lang";
export const THEME_KEY = "fs-theme";

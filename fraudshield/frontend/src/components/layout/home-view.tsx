"use client";

import Link from "next/link";

import { RecentScans } from "@/components/history/recent-scans";
import { Scanner } from "@/components/scanner/scanner";
import { ButtonLink, Card } from "@/components/ui/kit";
import { useMe } from "@/hooks/use-me";
import { usePrefs } from "@/i18n/provider";

const FEATURES = [
  { title: "home.feature1.title", body: "home.feature1.body", icon: "M12 2 4 5v6c0 5 3.400 9.400 8 11 4.600-1.600 8-6 8-11V5l-8-3z" },
  { title: "home.feature2.title", body: "home.feature2.body", icon: "M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8l-4 4V6a2 2 0 0 1 2-2z" },
  { title: "home.feature3.title", body: "home.feature3.body", icon: "M13 3a9 9 0 1 0 9 9h-2a7 7 0 1 1-7-7V3zm-1 5v5l4 2 .8-1.400-3.300-1.600V8H12z" },
] as const;

export function HomeView() {
  const { t } = usePrefs();
  const { loaded, me } = useMe();

  return (
    <main className="flex-1">
      <section className="hero-glow border-b border-line">
        <div className="mx-auto w-full max-w-2xl px-4 py-14 sm:py-20">
          <header className="mb-8 space-y-3 text-center">
            <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{t("home.title")}</h1>
            <p className="text-muted">{t("home.subtitle")}</p>
          </header>
          <Scanner />
          {loaded && !me && (
            <div className="mt-8 flex justify-center">
              <ButtonLink href="/register">{t("home.cta")}</ButtonLink>
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-12">
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="space-y-2">
              <svg viewBox="0 0 24 24" className="size-6 text-brand" fill="currentColor" aria-hidden="true">
                <path d={f.icon} />
              </svg>
              <h2 className="font-semibold tracking-tight">{t(f.title)}</h2>
              <p className="text-sm text-muted">{t(f.body)}</p>
            </Card>
          ))}
        </div>
        <div className="mx-auto mt-10 max-w-2xl">
          <RecentScans />
          <nav className="mt-8 flex justify-center gap-6 text-sm text-muted">
            <Link href="/report" className="underline">
              {t("nav.report")}
            </Link>
          </nav>
        </div>
      </section>
    </main>
  );
}

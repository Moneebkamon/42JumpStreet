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

const LAYERS = ["home.layer1", "home.layer2", "home.layer3", "home.layer4"] as const;

export function HomeView() {
  const { t } = usePrefs();
  const { loaded, me } = useMe();

  return (
    <main className="flex-1">
      <section className="hero-glow">
        <div className="mx-auto w-full max-w-3xl px-4 pt-16 pb-12 sm:pt-24">
          <header className="mb-10 space-y-5 text-center animate-fade-up">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/5 px-3 py-1 text-brand backdrop-blur">
              <span className="relative flex size-2">
                <span className="absolute inline-flex size-full rounded-full bg-brand animate-pulse-ring" />
                <span className="relative inline-flex size-2 rounded-full bg-brand" />
              </span>
              <span className="kicker" suppressHydrationWarning>
                {t("home.kicker")}
              </span>
            </div>
            <h1 className="text-gradient text-4xl font-semibold tracking-tight sm:text-6xl" suppressHydrationWarning>
              {t("home.title")}
            </h1>
            <p className="mx-auto max-w-xl text-muted sm:text-lg" suppressHydrationWarning>
              {t("home.subtitle")}
            </p>
          </header>

          <div className="glow-border glass rounded-2xl p-4 shadow-[0_30px_80px_-30px_var(--brand)] animate-fade-up [animation-delay:120ms] sm:p-5">
            <Scanner />
          </div>

          <div className="mt-8 animate-fade-up [animation-delay:240ms]">
            <p className="kicker mb-3 text-center text-muted" suppressHydrationWarning>
              {t("home.layers")}
            </p>
            <ol className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
              {LAYERS.map((key, i) => (
                <li
                  key={key}
                  className="group relative flex items-center gap-2 overflow-hidden rounded-xl border border-line bg-card px-3 py-2.5 text-foreground/90 backdrop-blur transition-colors hover:border-brand/40"
                >
                  <span className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand/60 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                  <span className="font-mono text-brand">0{i + 1}</span>
                  <span suppressHydrationWarning>{t(key)}</span>
                </li>
              ))}
            </ol>
          </div>

          {loaded && !me && (
            <div className="mt-10 flex justify-center">
              <ButtonLink href="/register" className="px-6 py-2.5">
                {t("home.cta")}
              </ButtonLink>
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-4 py-12">
        <div className="grid gap-4 md:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="group space-y-3 hover:-translate-y-0.5 transition-transform">
              <span className="grid size-10 place-items-center rounded-xl bg-gradient-to-br from-brand/20 to-brand-2/10 ring-1 ring-brand/30 transition group-hover:shadow-[0_0_24px_-4px_var(--brand)]">
                <svg viewBox="0 0 24 24" className="size-5 text-brand" fill="currentColor" aria-hidden="true">
                  <path d={f.icon} />
                </svg>
              </span>
              <h2 className="font-semibold tracking-tight">{t(f.title)}</h2>
              <p className="text-sm text-muted">{t(f.body)}</p>
            </Card>
          ))}
        </div>
        <div className="mx-auto mt-10 max-w-2xl">
          <RecentScans />
          <nav className="mt-8 flex justify-center gap-6 text-sm text-muted">
            <Link href="/report" className="underline decoration-brand/40 underline-offset-4 hover:text-foreground">
              {t("nav.report")}
            </Link>
          </nav>
        </div>
      </section>
    </main>
  );
}

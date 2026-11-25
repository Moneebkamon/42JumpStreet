"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { LanguageSwitch } from "@/components/layout/language-switch";
import { ButtonLink, ShieldLogo, cn } from "@/components/ui/kit";
import { announceAuthChange, useMe } from "@/hooks/use-me";
import type { MessageKey } from "@/i18n/config";
import { usePrefs } from "@/i18n/provider";
import { logout } from "@/lib/api-auth";

type NavLink = { href: string; key: MessageKey };

const PUBLIC_LINKS: NavLink[] = [
  { href: "/", key: "nav.check" },
  { href: "/report", key: "nav.report" },
];
const MEMBER_LINKS: NavLink[] = [
  { href: "/dashboard", key: "nav.dashboard" },
  { href: "/history", key: "nav.history" },
  // TODO(DELETE LATER - privacy): message watch list is switched off
  // { href: "/watchlist", key: "nav.watchlist" },
  { href: "/devices", key: "nav.devices" },
];
const STAFF_LINKS: NavLink[] = [
  { href: "/scan", key: "nav.recent" },
  { href: "/console", key: "nav.console" },
  { href: "/console/cases", key: "nav.cases" },
];
const ADMIN_LINKS: NavLink[] = [
  { href: "/admin/rules", key: "nav.scoring" },
  { href: "/admin/feedback", key: "nav.reviews" },
  { href: "/admin/audit", key: "nav.audit" },
];

function isActive(path: string, href: string): boolean {
  if (!path) return false;
  if (href === "/") return path === "/";
  if (href === "/console") return path === "/console";
  return path === href || path.startsWith(`${href}/`);
}

function Links({ path }: { path: string }) {
  const router = useRouter();
  const { t } = usePrefs();
  const { loaded, me } = useMe();
  const isStaff = me?.role === "analyst" || me?.role === "admin";
  const links = [
    ...PUBLIC_LINKS,
    ...(me ? MEMBER_LINKS : []),
    ...(isStaff ? STAFF_LINKS : []),
    ...(me?.role === "admin" ? ADMIN_LINKS : []),
  ];

  async function signOut() {
    await logout();
    announceAuthChange();
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-30 bg-background/60 backdrop-blur-xl">
      <nav aria-label="Main" className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-x-1 gap-y-2 px-4 py-2.5 text-sm">
        <Link href="/" className="me-4 flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-8 place-items-center rounded-lg bg-brand/10 ring-1 ring-brand/30">
            <ShieldLogo className="size-5 text-brand drop-shadow-[0_0_6px_var(--brand)]" />
          </span>
          <span suppressHydrationWarning className="text-[15px]">{t("brand")}</span>
        </Link>
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            aria-current={isActive(path, l.href) ? "page" : undefined}
            className={cn(
              "rounded-lg px-2.5 py-1.5 transition-colors",
              isActive(path, l.href)
                ? "bg-brand/10 font-medium text-foreground ring-1 ring-inset ring-brand/30"
                : "text-muted hover:bg-white/5 hover:text-foreground",
            )}
          >
            <span suppressHydrationWarning>{t(l.key)}</span>
          </Link>
        ))}
        <span className="ms-auto flex items-center gap-2">
          <LanguageSwitch />
          {loaded && me && me.auth_enabled !== false ? (
            <>
              <span className="hidden text-xs text-muted sm:inline">
                {me.username} · {t(`role.${me.role}` as MessageKey)}
              </span>
              <button type="button" onClick={signOut} className="rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-muted hover:text-foreground">
                {t("nav.signout")}
              </button>
            </>
          ) : loaded && !me ? (
            <>
              <Link href="/login" className="rounded-lg px-3 py-1.5 text-sm text-muted hover:text-foreground">
                {t("nav.signin")}
              </Link>
              <ButtonLink href="/register">{t("nav.signup")}</ButtonLink>
            </>
          ) : null}
        </span>
      </nav>
      <div className="h-px w-full bg-gradient-to-r from-transparent via-brand/50 to-transparent" />
    </header>
  );
}

/** Highlights the current page. Reads the path at request time, so render it inside <Suspense>. */
export function Navbar() {
  return <Links path={usePathname()} />;
}

/** The same links without the highlight: shown while the path is not known yet. */
export function NavbarFallback() {
  return <Links path="" />;
}

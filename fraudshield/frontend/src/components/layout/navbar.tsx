"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { announceAuthChange, useMe } from "@/hooks/use-me";
import { logout } from "@/lib/api-auth";

const PUBLIC_LINKS = [
  { href: "/", label: "Check a link" },
  { href: "/scan", label: "Recent scans" },
  { href: "/report", label: "Report a scam" },
];
const STAFF_LINKS = [
  { href: "/console", label: "Early detection" },
  { href: "/console/cases", label: "Cases" },
];
const ADMIN_LINKS = [
  { href: "/admin/rules", label: "Scoring" },
  { href: "/admin/feedback", label: "Reviews" },
  { href: "/admin/audit", label: "Audit log" },
];

function isActive(path: string, href: string): boolean {
  if (!path) return false;
  if (href === "/") return path === "/";
  if (href === "/console") return path === "/console";
  return path === href || path.startsWith(`${href}/`);
}

function Links({ path }: { path: string }) {
  const router = useRouter();
  const { loaded, me } = useMe();
  const links = [...PUBLIC_LINKS, ...(me ? STAFF_LINKS : []), ...(me?.role === "admin" ? ADMIN_LINKS : [])];

  async function signOut() {
    await logout();
    announceAuthChange();
    router.push("/");
  }

  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800">
      <nav aria-label="Main" className="mx-auto flex w-full max-w-5xl flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 text-sm">
        <Link href="/" className="mr-2 font-semibold tracking-tight">
          FraudShield
        </Link>
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            aria-current={isActive(path, l.href) ? "page" : undefined}
            className={
              isActive(path, l.href)
                ? "font-medium underline underline-offset-4"
                : "text-zinc-600 hover:underline dark:text-zinc-400"
            }
          >
            {l.label}
          </Link>
        ))}
        <span className="ml-auto flex items-center gap-3 text-xs text-zinc-500">
          {loaded && me && me.auth_enabled !== false ? (
            <>
              <span>
                {me.username} ({me.role})
              </span>
              <button type="button" onClick={signOut} className="underline">
                Sign out
              </button>
            </>
          ) : loaded && !me ? (
            <Link href="/login" className="underline">
              Staff sign-in
            </Link>
          ) : null}
        </span>
      </nav>
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

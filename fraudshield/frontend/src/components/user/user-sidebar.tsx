"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/components/ui/kit";
import type { MessageKey } from "@/i18n/config";
import { usePrefs } from "@/i18n/provider";

const ITEMS: { href: string; key: MessageKey; icon: string }[] = [
  { href: "/dashboard", key: "nav.dashboard", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { href: "/history", key: "nav.history", icon: "M13 3a9 9 0 1 0 9 9h-2a7 7 0 1 1-7-7V3zm-1 5v5l4 2 .8-1.4-3.3-1.6V8H12z" },
  // TODO(DELETE LATER - privacy): message watch list is switched off
  // { href: "/watchlist", key: "nav.watchlist", icon: "M12 4.5C7 4.5 2.7 7.6 1 12c1.7 4.4 6 7.5 11 7.5s9.3-3.100 11-7.500c-1.700-4.400-6-7.500-11-7.500zm0 12.500a5 5 0 1 1 0-10 5 5 0 0 1 0 10zm0-8a3 3 0 1 0 0 6 3 3 0 0 0 0-6z" },
  { href: "/devices", key: "nav.devices", icon: "M20.5 11H19V7a2 2 0 0 0-2-2h-4V3.500a2.500 2.500 0 0 0-5 0V5H4a2 2 0 0 0-2 2v3.800h1.500a2.700 2.700 0 0 1 0 5.400H2V20a2 2 0 0 0 2 2h3.800v-1.500a2.700 2.700 0 0 1 5.400 0V22H17a2 2 0 0 0 2-2v-4h1.500a2.500 2.500 0 0 0 0-5z" },
  { href: "/settings", key: "nav.settings", icon: "M19.400 13a7.500 7.500 0 0 0 0-2l2.100-1.600-2-3.400-2.500 1a7.600 7.600 0 0 0-1.700-1L15 3h-4l-.4 3a7.600 7.600 0 0 0-1.700 1l-2.500-1-2 3.400L6.600 11a7.500 7.500 0 0 0 0 2l-2.100 1.600 2 3.400 2.500-1c.5.400 1.100.7 1.700 1l.4 3h4l.4-3c.6-.3 1.200-.6 1.700-1l2.500 1 2-3.400-2.100-1.600zM12 15.500a3.500 3.500 0 1 1 0-7 3.500 3.500 0 0 1 0 7z" },
];

export function UserSidebar() {
  const path = usePathname();
  const { t } = usePrefs();
  return (
    <aside className="md:w-52 md:shrink-0">
      <nav aria-label="Account" className="flex gap-1 overflow-x-auto md:sticky md:top-20 md:flex-col">
        {ITEMS.map((i) => {
          const active = path === i.href || path.startsWith(`${i.href}/`);
          return (
            <Link
              key={i.href}
              href={i.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm transition-colors",
                active ? "bg-brand/15 font-medium text-brand" : "text-muted hover:bg-zinc-200/60 hover:text-foreground dark:hover:bg-zinc-800",
              )}
            >
              <svg viewBox="0 0 24 24" className="size-4 shrink-0" fill="currentColor" aria-hidden="true">
                <path d={i.icon} />
              </svg>
              {t(i.key)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

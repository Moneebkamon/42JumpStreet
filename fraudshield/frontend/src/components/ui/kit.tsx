import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

/** Small shared UI kit in the Beyin shadcn style: cards, buttons, badges, switch, stat tiles. */

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

const BTN_BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
const BTN_VARIANT = {
  primary: "bg-brand text-brand-ink hover:brightness-110",
  secondary: "border border-line bg-card text-foreground hover:bg-zinc-100 dark:hover:bg-zinc-800",
  danger: "border border-red-500/40 bg-red-500/10 text-red-600 hover:bg-red-500/20 dark:text-red-400",
  ghost: "text-muted hover:text-foreground",
} as const;
export type ButtonVariant = keyof typeof BTN_VARIANT;

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button className={cn(BTN_BASE, BTN_VARIANT[variant], className)} {...props} />;
}

export function ButtonLink({
  href,
  variant = "primary",
  className,
  children,
}: {
  href: string;
  variant?: ButtonVariant;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={cn(BTN_BASE, BTN_VARIANT[variant], className)}>
      {children}
    </Link>
  );
}

export const FIELD =
  "block w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-foreground placeholder:text-zinc-500 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(FIELD, className)} {...props} />;
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cn("rounded-2xl border border-line bg-card p-5", className)}>{children}</section>;
}

export function CardTitle({ children, hint }: { children: ReactNode; hint?: ReactNode }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-3">
      <h2 className="text-sm font-semibold tracking-tight">{children}</h2>
      {hint && <div className="text-xs text-muted">{hint}</div>}
    </div>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="max-w-2xl text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

const TONES = {
  neutral: "bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  safe: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
  warn: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300",
  bad: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  info: "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300",
} as const;
export type Tone = keyof typeof TONES;

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={cn("inline-block rounded-full px-2.5 py-0.5 text-xs font-medium", TONES[tone])}>{children}</span>;
}

export const BAND_TONE: Record<string, Tone> = { safe: "safe", suspicious: "warn", high_risk: "high", likely_fraud: "bad" };
export const BAND_LABEL: Record<string, string> = {
  safe: "Looks safe",
  suspicious: "Suspicious",
  high_risk: "High risk",
  likely_fraud: "Likely fraud",
};

export function BandBadge({ band }: { band: string }) {
  return <Badge tone={BAND_TONE[band] ?? "neutral"}>{BAND_LABEL[band] ?? band}</Badge>;
}

export function Switch({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative h-6 w-11 shrink-0 rounded-full border border-line transition-colors disabled:opacity-50",
        checked ? "bg-brand" : "bg-zinc-300 dark:bg-zinc-700",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 size-5 rounded-full bg-white shadow transition-all",
          checked ? "start-[1.375rem]" : "start-0.5",
        )}
      />
    </button>
  );
}

export function StatTile({ label, value, tone }: { label: string; value: ReactNode; tone?: "bad" }) {
  return (
    <div className="rounded-2xl border border-line bg-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className={cn("mt-1 text-3xl font-semibold tabular-nums", tone === "bad" && "text-red-500")}>{value}</div>
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "error" | "ok"; children: ReactNode }) {
  const cls = {
    info: "border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300",
    error: "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300",
    ok: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  }[tone];
  return (
    <p role={tone === "error" ? "alert" : "status"} className={cn("rounded-xl border px-4 py-3 text-sm", cls)}>
      {children}
    </p>
  );
}

export function ShieldLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className ?? "size-6"} fill="none" aria-hidden="true">
      <path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3z" fill="currentColor" opacity=".18" />
      <path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path d="m8.5 12 2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

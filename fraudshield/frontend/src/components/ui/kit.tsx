import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

/** Small shared UI kit in the Beyin shadcn style: cards, buttons, badges, switch, stat tiles. */

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

const BTN_BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50";
const BTN_VARIANT = {
  primary:
    "bg-gradient-to-r from-brand to-brand-2 text-brand-ink shadow-[0_6px_24px_-8px_var(--brand)] hover:-translate-y-px hover:shadow-[0_10px_30px_-8px_var(--brand)] active:translate-y-0",
  secondary: "glass border border-line text-foreground hover:border-brand/40 hover:bg-zinc-100 dark:hover:bg-brand/5",
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
  "block w-full rounded-lg border border-zinc-300 bg-white px-3 dark:border-zinc-700 dark:bg-zinc-950/70 py-2 text-sm text-foreground placeholder:text-zinc-500 outline-none transition focus:border-brand/70 focus:ring-2 focus:ring-brand/20";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(FIELD, className)} {...props} />;
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <section
      className={cn(
        "glass rounded-2xl border border-line p-5 shadow-[inset_0_1px_0_0_rgb(255_255_255/0.04),0_20px_40px_-24px_rgb(0_0_0/0.6)] transition-colors hover:border-brand/25",
        className,
      )}
    >{children}</section>;
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
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
        <div className="h-px w-16 bg-gradient-to-r from-brand to-transparent" />
        {subtitle && <p className="max-w-2xl text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

const TONES = {
  neutral: "bg-zinc-200 text-zinc-700 ring-1 ring-inset ring-zinc-500/20 dark:bg-zinc-800/70 dark:text-zinc-300",
  safe: "bg-emerald-100 text-emerald-800 ring-1 ring-inset ring-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300",
  warn: "bg-amber-100 text-amber-800 ring-1 ring-inset ring-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300",
  high: "bg-orange-100 text-orange-800 ring-1 ring-inset ring-orange-500/30 dark:bg-orange-500/10 dark:text-orange-300",
  bad: "bg-red-100 text-red-800 ring-1 ring-inset ring-red-500/40 dark:bg-red-500/10 dark:text-red-300",
  info: "bg-sky-100 text-sky-800 ring-1 ring-inset ring-sky-500/30 dark:bg-sky-500/10 dark:text-sky-300",
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
        checked ? "bg-brand shadow-[0_0_14px_-2px_var(--brand)]" : "bg-zinc-300 dark:bg-zinc-700",
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
    <div className="glass group relative overflow-hidden rounded-2xl border border-line p-4 transition-colors hover:border-brand/30">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand/60 to-transparent opacity-60 group-hover:opacity-100" />
      <div className="kicker text-muted">{label}</div>
      <div className={cn("mt-1 text-3xl font-semibold tabular-nums", tone === "bad" ? "text-threat" : "text-foreground")}>{value}</div>
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
    <p role={tone === "error" ? "alert" : "status"} className={cn("rounded-xl border px-4 py-3 text-sm backdrop-blur", cls)}>
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

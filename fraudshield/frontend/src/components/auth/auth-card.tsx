import { ShieldLogo } from "@/components/ui/kit";

/** Centered card used by the sign-in and sign-up pages. */
export function AuthCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <main className="hero-glow flex flex-1 items-center justify-center px-4 py-14">
      <div className="w-full max-w-sm space-y-6 glow-border glass rounded-2xl border border-line p-7 shadow-[0_30px_80px_-30px_var(--brand)] animate-fade-up">
        <header className="space-y-2 text-center">
          <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-brand/10 ring-1 ring-brand/30"><ShieldLogo className="size-8 text-brand drop-shadow-[0_0_8px_var(--brand)]" /></span>
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          <p className="text-sm text-muted">{subtitle}</p>
        </header>
        {children}
      </div>
    </main>
  );
}

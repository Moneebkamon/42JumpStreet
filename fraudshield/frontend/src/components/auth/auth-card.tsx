import { ShieldLogo } from "@/components/ui/kit";

/** Centered card used by the sign-in and sign-up pages. */
export function AuthCard({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <main className="hero-glow flex flex-1 items-center justify-center px-4 py-14">
      <div className="w-full max-w-sm space-y-6 rounded-2xl border border-line bg-card p-7 shadow-xl shadow-black/5">
        <header className="space-y-2 text-center">
          <ShieldLogo className="mx-auto size-10 text-brand" />
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          <p className="text-sm text-muted">{subtitle}</p>
        </header>
        {children}
      </div>
    </main>
  );
}

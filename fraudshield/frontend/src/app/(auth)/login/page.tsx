import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <main className="mx-auto w-full max-w-sm flex-1 space-y-6 px-4 py-16">
      <header className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">Staff sign-in</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">For FraudShield analysts and administrators.</p>
      </header>
      <LoginForm />
      <p className="text-center text-xs text-zinc-500">
        Checking a link and reporting a scam do not need an account.
      </p>
    </main>
  );
}

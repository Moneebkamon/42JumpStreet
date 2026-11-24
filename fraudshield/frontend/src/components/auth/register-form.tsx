"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Input, Notice } from "@/components/ui/kit";
import { announceAuthChange } from "@/hooks/use-me";
import { usePrefs } from "@/i18n/provider";
import { register } from "@/lib/api-auth";

export function RegisterForm() {
  const router = useRouter();
  const { t } = usePrefs();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await register(username.trim(), email.trim(), password);
      announceAuthChange();
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("auth.username")}</span>
        <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" minLength={3} maxLength={40} required />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("auth.email")}</span>
        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("auth.password")}</span>
        <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" minLength={8} required />
        <span className="text-xs text-muted">{t("auth.password.hint")}</span>
      </label>
      {error && <Notice tone="error">{error}</Notice>}
      <Button type="submit" disabled={busy || !username.trim() || !email.trim() || password.length < 8} className="w-full">
        {busy ? "..." : t("nav.signup")}
      </Button>
      <p className="text-center text-sm text-muted">
        {t("auth.have")}{" "}
        <Link href="/login" className="font-medium text-brand underline">
          {t("nav.signin")}
        </Link>
      </p>
    </form>
  );
}

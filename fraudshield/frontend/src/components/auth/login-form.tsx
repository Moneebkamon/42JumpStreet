"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Input, Notice } from "@/components/ui/kit";
import { announceAuthChange } from "@/hooks/use-me";
import { usePrefs } from "@/i18n/provider";
import { isStaffRole, login } from "@/lib/api-auth";

export function LoginForm() {
  const router = useRouter();
  const { t } = usePrefs();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await login(username.trim(), password);
      announceAuthChange();
      router.push(isStaffRole(me.role) ? "/console" : "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("auth.username")}</span>
        <Input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
      </label>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">{t("auth.password")}</span>
        <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
      </label>
      {error && <Notice tone="error">{error}</Notice>}
      <Button type="submit" disabled={busy || !username.trim() || !password} className="w-full">
        {busy ? "..." : t("nav.signin")}
      </Button>
      <p className="text-center text-sm text-muted">
        {t("auth.new")}{" "}
        <Link href="/register" className="font-medium text-brand underline">
          {t("nav.signup")}
        </Link>
      </p>
    </form>
  );
}

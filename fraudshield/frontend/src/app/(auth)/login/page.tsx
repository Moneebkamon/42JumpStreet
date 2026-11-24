"use client";

import { AuthCard } from "@/components/auth/auth-card";
import { LoginForm } from "@/components/auth/login-form";
import { usePrefs } from "@/i18n/provider";

export default function LoginPage() {
  const { t } = usePrefs();
  return (
    <AuthCard title={t("auth.signin.title")} subtitle={t("auth.signin.subtitle")}>
      <LoginForm />
    </AuthCard>
  );
}

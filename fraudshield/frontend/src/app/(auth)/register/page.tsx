"use client";

import { AuthCard } from "@/components/auth/auth-card";
import { RegisterForm } from "@/components/auth/register-form";
import { usePrefs } from "@/i18n/provider";

export default function RegisterPage() {
  const { t } = usePrefs();
  return (
    <AuthCard title={t("auth.signup.title")} subtitle={t("auth.signup.subtitle")}>
      <RegisterForm />
    </AuthCard>
  );
}

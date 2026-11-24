"use client";

import { ButtonLink } from "@/components/ui/kit";
import { useMe } from "@/hooks/use-me";
import { usePrefs } from "@/i18n/provider";

/** Shows its children to any signed-in account (member, analyst or admin). The API enforces this too. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { loaded, me } = useMe();
  const { t } = usePrefs();

  if (!loaded) {
    return (
      <p role="status" className="text-sm text-muted">
        {t("common.loading")}
      </p>
    );
  }
  if (!me) {
    return (
      <div className="mx-auto max-w-md space-y-4 rounded-2xl border border-line bg-card p-8 text-center">
        <h2 className="text-lg font-semibold">{t("common.signin.required")}</h2>
        <div className="flex justify-center gap-3">
          <ButtonLink href="/login">{t("nav.signin")}</ButtonLink>
          <ButtonLink href="/register" variant="secondary">
            {t("nav.signup")}
          </ButtonLink>
        </div>
      </div>
    );
  }
  return <>{children}</>;
}

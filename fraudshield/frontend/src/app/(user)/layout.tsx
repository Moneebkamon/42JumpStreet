import { Suspense } from "react";

import { RequireAuth } from "@/components/auth/require-auth";
import { UserSidebar } from "@/components/user/user-sidebar";

// Members' pages render only after the session check in the browser, so there is nothing to validate for instant navigation.
export const instant = false;

/** Shell for the signed-in member area: sidebar on the side, content next to it. */
export default function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8 md:flex-row">
      <Suspense fallback={null}>
        <UserSidebar />
      </Suspense>
      <main className="min-w-0 flex-1">
        <RequireAuth>{children}</RequireAuth>
      </main>
    </div>
  );
}

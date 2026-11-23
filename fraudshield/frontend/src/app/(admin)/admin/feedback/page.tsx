import { FeedbackQueue } from "@/components/admin/feedback-queue";
import { RequireStaff } from "@/components/auth/require-staff";

export default function FeedbackPage() {
  return (
    <main className="mx-auto w-full max-w-4xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">False-positive review</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          When someone says a flagged link is safe, an administrator decides here whether the domain should be allowlisted.
          Every decision needs a reason and is written to the audit log.
        </p>
      </header>
      <RequireStaff admin>
        <FeedbackQueue />
      </RequireStaff>
    </main>
  );
}

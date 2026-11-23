import { RequireStaff } from "@/components/auth/require-staff";
import { CaseList } from "@/components/cases/case-list";

export default function CasesPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Cases</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Each case follows a suspected scam site from first review to takedown, with a recorded reason for every
          status change.
        </p>
      </header>
      <RequireStaff>
        <CaseList />
      </RequireStaff>
    </main>
  );
}

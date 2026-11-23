import { RequireStaff } from "@/components/auth/require-staff";
import { RulesEditor } from "@/components/admin/rules-editor";

export default function RulesPage() {
  return (
    <main className="mx-auto w-full max-w-4xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Scoring settings</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Change how much each warning sign counts and where the risk bands start, without redeploying. Every change needs
          a reason and is kept in the history and the audit log. Official-domain and threat-feed overrides stay fixed.
        </p>
      </header>
      <RequireStaff admin>
        <RulesEditor />
      </RequireStaff>
    </main>
  );
}

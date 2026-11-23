import { RequireStaff } from "@/components/auth/require-staff";
import { AuditLog } from "@/components/admin/audit-log";

export default function AuditPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Who did what and when: case changes, evidence freezes, views and hash checks, drafts and exports. Entries cannot
          be edited or deleted. There is no login yet, so the name shown is a label, not a verified identity.
        </p>
      </header>
      <RequireStaff admin>
        <AuditLog />
      </RequireStaff>
    </main>
  );
}

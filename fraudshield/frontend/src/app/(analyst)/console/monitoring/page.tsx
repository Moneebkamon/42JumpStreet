import { RequireStaff } from "@/components/auth/require-staff";
import { CheckedDomains } from "@/components/feed/checked-domains";
import { FeedDashboard } from "@/components/feed/feed-dashboard";

export default function MonitoringPage() {
  return (
    <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Monitoring</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Every suspicious website the early-detection feed has scored, with filters. Search and map monitoring come in a
          later stage.
        </p>
      </header>
      <RequireStaff>
        <FeedDashboard />
        <CheckedDomains />
      </RequireStaff>
    </main>
  );
}

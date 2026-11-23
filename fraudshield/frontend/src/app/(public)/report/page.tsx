import { CitizenReportForm } from "@/components/report/citizen-report-form";

export default function ReportPage() {
  return (
    <main className="mx-auto w-full max-w-xl flex-1 space-y-6 px-4 py-10">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Report a scam</h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          Received a suspicious link by SMS, email or social media? Tell us. Analysts use reports to decide what to
          investigate first.
        </p>
      </header>
      <CitizenReportForm />
    </main>
  );
}

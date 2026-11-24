"use client";

import Link from "next/link";

import { useMe } from "@/hooks/use-me";

/** Shows its children only to signed-in staff (and only to admins when `admin` is set). The API enforces this too. */
export function RequireStaff({ admin = false, children }: { admin?: boolean; children: React.ReactNode }) {
  const { loaded, me } = useMe();

  if (!loaded) {
    return (
      <p role="status" className="text-sm text-zinc-500">
        Checking your sign-in...
      </p>
    );
  }
  if (!me) {
    return (
      <div className="space-y-3 rounded-2xl border border-zinc-200 p-6 text-center dark:border-zinc-800">
        <h2 className="text-lg font-semibold">Staff sign-in required</h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">This area is for Manee analysts.</p>
        <Link href="/login" className="inline-block rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-zinc-100 dark:text-zinc-900">
          Sign in
        </Link>
      </div>
    );
  }
  if (me.role === "user") {
    return (
      <p role="alert" className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
        This area is for Manee staff. Your account ({me.username}) is a regular member account.{" "}
        <Link href="/dashboard" className="underline">
          Go to your dashboard
        </Link>
        .
      </p>
    );
  }
  if (admin && me.role !== "admin") {
    return (
      <p role="alert" className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-200">
        This page needs an administrator. You are signed in as {me.username} (analyst).
      </p>
    );
  }
  return <>{children}</>;
}

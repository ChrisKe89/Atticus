import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Check your inbox · Atticus",
};

export default function VerifyRequestPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col items-center gap-4 text-center">
      <span className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-500">
        ✓
      </span>
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Magic link sent</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          We sent you an email with a secure link. Open it on this device to complete sign-in.
        </p>
      </div>
    </div>
  );
}

import type { Metadata } from "next";
import Link from "next/link";
import { SignInForm } from "@/components/auth/sign-in-form";

export const metadata: Metadata = {
  title: "Sign in · Atticus",
};

export default function SignInPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6 text-center">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-widest text-indigo-500">Access</p>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
          Sign in to Atticus
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Use your company email to receive a secure, single-use magic link.
        </p>
      </div>
      <SignInForm />
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Need access? Contact an administrator or{" "}
        <Link className="font-semibold text-indigo-600 hover:underline" href="/contact">
          submit a request
        </Link>
        .
      </p>
    </div>
  );
}

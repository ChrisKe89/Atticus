'use client';

import { FormEvent, useState, useTransition } from 'react';
import { signIn } from 'next-auth/react';

export function SignInForm() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    startTransition(async () => {
      const result = await signIn('email', {
        email,
        redirect: false,
      });
      if (result?.error) {
        setError('We could not send a magic link to that address. Ensure you are provisioned.');
        setSent(false);
        return;
      }
      setSent(true);
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="space-y-2">
        <label htmlFor="email" className="text-sm font-medium text-slate-800 dark:text-slate-200">
          Work email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
          placeholder="alex@contoso.com"
          autoComplete="email"
        />
      </div>
      <button
        type="submit"
        disabled={isPending || sent}
        className="w-full rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-400"
      >
        {sent ? 'Magic link sent' : isPending ? 'Sending...' : 'Email me a magic link'}
      </button>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {sent ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Check your inbox for a sign-in email from Atticus. The link expires in 10 minutes.
        </p>
      ) : null}
    </form>
  );
}

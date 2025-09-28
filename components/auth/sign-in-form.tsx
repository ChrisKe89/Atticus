'use client';

import { FormEvent, useState, useTransition } from 'react';
import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

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
      <div className="space-y-2 text-left">
        <Label htmlFor="email">Work email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="alex@contoso.com"
          autoComplete="email"
        />
      </div>
      <Button type="submit" className="w-full" disabled={isPending || sent}>
        {sent ? 'Magic link sent' : isPending ? 'Sending...' : 'Email me a magic link'}
      </Button>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {sent ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Check your inbox for a sign-in email from Atticus. The link expires in 10 minutes.
        </p>
      ) : null}
    </form>
  );
}

import type { Metadata } from 'next';
import Link from 'next/link';
import { Shield, Zap } from 'lucide-react';
import { PageHeader } from '@/components/page-header';

const toggles = [
  {
    id: 'escalations',
    label: 'Escalate low-confidence answers',
    description: 'Automatically open an escalation email when answer confidence drops below the policy threshold.',
    defaultChecked: true,
  },
  {
    id: 'request-logging',
    label: 'Attach anonymised request logs',
    description: 'Include hashed user IDs and request IDs so admins can correlate tickets with chat sessions.',
    defaultChecked: true,
  },
  {
    id: 'typing-preview',
    label: 'Streaming responses',
    description: 'Show tokens as they are generated for faster operator feedback.',
    defaultChecked: false,
  },
];

export const metadata: Metadata = {
  title: 'Settings · Atticus',
};

export default function SettingsPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
      <PageHeader
        eyebrow="Settings"
        title="Workspace preferences"
        description="Configure escalation behaviour, logging guardrails, and chat defaults."
        actions={
          <Link
            href="/admin"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-indigo-400 hover:text-indigo-600 dark:border-slate-700 dark:text-slate-200 dark:hover:border-indigo-500"
          >
            View admin console
          </Link>
        }
      />

      <section className="space-y-6">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-500">Policies</h2>
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {toggles.map((toggle) => (
            <label key={toggle.id} htmlFor={toggle.id} className="flex flex-col gap-2 rounded-2xl border border-transparent p-4 transition hover:border-indigo-200 dark:hover:border-indigo-500/40">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{toggle.label}</p>
                  <p id={`${toggle.id}-description`} className="text-xs text-slate-500 dark:text-slate-400">
                    {toggle.description}
                  </p>
                </div>
                <input
                  id={toggle.id}
                  type="checkbox"
                  defaultChecked={toggle.defaultChecked}
                  className="h-5 w-10 cursor-pointer appearance-none rounded-full border border-slate-300 bg-slate-200 transition before:block before:h-4 before:w-4 before:translate-x-0 before:rounded-full before:bg-white before:shadow before:transition checked:border-indigo-400 checked:bg-indigo-500 checked:before:translate-x-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:checked:border-indigo-400 dark:checked:bg-indigo-500"
                  aria-describedby={`${toggle.id}-description`}
                />
              </div>
            </label>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
            <Shield className="h-5 w-5" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Safety guardrails</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Escalation allow-lists and role-based policies ensure sensitive documents never leave your tenant.
          </p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
            <Zap className="h-5 w-5" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Performance tuning</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Adjust search probes, reranker policies, and streaming defaults to match your team&apos;s workflow.
          </p>
        </article>
      </section>
    </div>
  );
}

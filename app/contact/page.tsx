import type { Metadata } from 'next';
import { MailCheck, PhoneCall } from 'lucide-react';
import { PageHeader } from '@/components/page-header';

export const metadata: Metadata = {
  title: 'Contact · Atticus',
};

export default function ContactPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
      <PageHeader
        eyebrow="Escalations"
        title="Raise an escalation"
        description="Submit production issues or low-confidence answers and the Atticus team will receive the full trace payload."
      />

      <form className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="grid gap-6 md:grid-cols-2">
          <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
            <span className="font-semibold">Name</span>
            <input
              type="text"
              name="name"
              placeholder="Alex Finnegan"
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
              required
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
            <span className="font-semibold">Work email</span>
            <input
              type="email"
              name="email"
              placeholder="alex@contoso.com"
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
              required
            />
          </label>
        </div>
        <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
          <span className="font-semibold">Issue summary</span>
          <input
            type="text"
            name="summary"
            placeholder="Low confidence response for Managed Print RFP"
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm transition focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
            required
          />
        </label>
        <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
          <span className="font-semibold">Details</span>
          <textarea
            name="details"
            rows={5}
            placeholder="Share the question, customer, and any attachments that should be included in the follow-up."
            className="rounded-2xl border border-slate-300 bg-white px-3 py-3 text-sm leading-6 text-slate-900 shadow-sm transition focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
            required
          />
        </label>
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
        >
          Submit escalation
          <MailCheck className="h-4 w-4" aria-hidden="true" />
        </button>
      </form>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">Preferred escalation window</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Monday–Friday, 08:00–18:00 local time. After hours requests receive an automated acknowledgement with the request ID.
          </p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
            <PhoneCall className="h-5 w-5" aria-hidden="true" />
          </div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">Urgent support</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Call +1 (555) 010-8890 and quote the request ID returned in your escalation receipt. PII is redacted in all logs.
          </p>
        </article>
      </section>
    </div>
  );
}

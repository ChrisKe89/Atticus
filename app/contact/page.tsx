import type { Metadata } from 'next';
import { MailCheck, PhoneCall } from 'lucide-react';
import { PageHeader } from '@/components/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

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
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" name="name" placeholder="Alex Finnegan" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" name="email" type="email" placeholder="alex@contoso.com" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="summary">Issue summary</Label>
          <Input
            id="summary"
            name="summary"
            placeholder="Low confidence response for Managed Print RFP"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="details">Details</Label>
          <Textarea
            id="details"
            name="details"
            rows={5}
            placeholder="Share the question, customer, and any attachments that should be included in the follow-up."
            required
          />
        </div>
        <Button type="submit" className="inline-flex items-center gap-2 rounded-full px-5 py-2.5">
          Submit escalation
          <MailCheck className="h-4 w-4" aria-hidden="true" />
        </Button>
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

import Link from 'next/link';
import { ArrowRight, Paperclip, Send, ShieldCheck, Sparkles } from 'lucide-react';
import { PageHeader } from '@/components/page-header';

const shortcuts = [
  { label: 'Shift + Enter', description: 'New line' },
  { label: 'Ctrl + Enter', description: 'Send message' },
  { label: 'Esc', description: 'Clear composer' },
];

const highlights = [
  {
    title: 'Grounded responses',
    description: 'Atticus cites every answer with the supporting evidence so Sales stays audit-ready.',
    icon: ShieldCheck,
  },
  {
    title: 'Fast ingest pipeline',
    description: 'Deterministic chunking keeps the knowledge base fresh without manual clean-up.',
    icon: Sparkles,
  },
];

export default function HomePage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12">
      <PageHeader
        eyebrow="Chat"
        title="Your Atticus workspace"
        description="Respond to tenders, proposals, and in-flight escalations with grounded answers."
        actions={
          <Link
            href="/apps"
            className="inline-flex items-center gap-2 rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
          >
            Explore integrations
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        }
      />

      <section className="grid gap-10 lg:grid-cols-[1.2fr_1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Live conversation</h2>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
              Connected
            </span>
          </div>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">A</div>
              <div className="flex-1 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 dark:bg-slate-800/60 dark:text-slate-200">
                Hi! Drop any tender or product question below and I will back it with citations from your latest content set.
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                You
              </div>
              <div className="flex-1 rounded-2xl bg-white p-4 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-100 dark:ring-slate-800">
                Can you outline the implementation timeline for the managed print service pilot?
              </div>
            </div>
          </div>
          <div className="mt-6 rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
            <div className="flex items-end gap-3">
              <button
                type="button"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <Paperclip className="h-5 w-5" aria-hidden="true" />
                <span className="sr-only">Attach file</span>
              </button>
              <label htmlFor="chat-message" className="sr-only">
                Message Atticus
              </label>
              <textarea
                id="chat-message"
                rows={3}
                placeholder="Message Atticus…"
                className="min-h-[72px] max-h-[160px] w-full resize-y rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
              />
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
                <span>Send</span>
              </button>
            </div>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex flex-wrap gap-3">
                {shortcuts.map((shortcut) => (
                  <span key={shortcut.label} className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
                    {shortcut.label} · {shortcut.description}
                  </span>
                ))}
              </div>
              <span className="truncate text-xs text-slate-400">No file attached</span>
            </div>
          </div>
        </div>
        <aside className="flex flex-col gap-6">
          {highlights.map((item) => (
            <article key={item.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-3 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
                <item.icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{item.title}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{item.description}</p>
            </article>
          ))}
        </aside>
      </section>
    </div>
  );
}

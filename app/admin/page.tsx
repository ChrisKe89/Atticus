import type { Metadata } from 'next';
import { Activity, Database, Folder, Users } from 'lucide-react';
import { PageHeader } from '@/components/page-header';

const panels = [
  {
    title: 'System activity',
    description: 'Live logs from ingestion, retrieval, and escalation workers.',
    icon: Activity,
    items: [
      'Real-time request IDs with latency histograms',
      'Escalation attempts with masked payload metadata',
      'Vector search probes and IVFFlat statistics',
    ],
  },
  {
    title: 'User roster',
    description: 'Manage RBAC roles and enforce org-level segregation.',
    icon: Users,
    items: ['Invite new teammates via magic link', 'Assign admin/reviewer roles', 'View last active session'],
  },
  {
    title: 'Content health',
    description: 'Track ingestion status and data freshness across products.',
    icon: Folder,
    items: ['Chunk coverage by document type', 'Footnote/table extraction success', 'SHA-256 drift detection'],
  },
  {
    title: 'Database metrics',
    description: 'pgvector statistics with quality guardrails.',
    icon: Database,
    items: ['IVFFlat list/probe recommendations', 'Recall@k snapshots by corpus', 'Storage growth and vacuum cadence'],
  },
];

export const metadata: Metadata = {
  title: 'Admin · Atticus',
};

export default function AdminPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <PageHeader
        eyebrow="Admin"
        title="Operations and governance"
        description="Monitor escalation volume, tune retrieval quality, and manage access policies."
      />

      <section className="grid gap-6 md:grid-cols-2">
        {panels.map((panel) => (
          <article key={panel.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
              <panel.icon className="h-5 w-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">{panel.title}</h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{panel.description}</p>
            <ul className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              {panel.items.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-indigo-500" aria-hidden="true" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </div>
  );
}

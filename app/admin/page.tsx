import type { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { Activity, Database, Folder, Users } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { GlossaryStatus, Role } from '@prisma/client';
import { PageHeader } from '@/components/page-header';
import { getServerAuthSession } from '@/lib/auth';
import { withRlsContext } from '@/lib/rls';
import { GlossaryAdminPanel, GlossaryEntryDto } from '@/components/glossary/admin-panel';

const panels: Array<{
  title: string;
  description: string;
  icon: LucideIcon;
  items: string[];
}> = [
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

type GlossaryEntryRecord = {
  id: string;
  term: string;
  definition: string;
  synonyms: string[];
  status: GlossaryStatus;
  createdAt: Date;
  updatedAt: Date;
  reviewedAt: Date | null;
  reviewNotes: string | null;
  author: { id: string; email: string | null; name: string | null } | null;
  updatedBy: { id: string; email: string | null; name: string | null } | null;
  reviewer: { id: string; email: string | null; name: string | null } | null;
};

export default async function AdminPage() {
  const session = await getServerAuthSession();
  if (!session) {
    redirect('/signin?from=/admin');
  }
  if (session.user.role !== Role.ADMIN) {
    redirect('/');
  }

  const rawEntries = await withRlsContext(session, (tx) =>
    tx.glossaryEntry.findMany({
      orderBy: { term: 'asc' },
      include: {
        author: { select: { id: true, email: true, name: true } },
        updatedBy: { select: { id: true, email: true, name: true } },
        reviewer: { select: { id: true, email: true, name: true } },
      },
    } as any)
  );
  const entries = rawEntries as unknown as GlossaryEntryRecord[];

  const glossaryEntries: GlossaryEntryDto[] = entries.map((entry) => ({
    id: entry.id,
    term: entry.term,
    definition: entry.definition,
    synonyms: entry.synonyms,
    status: entry.status,
    createdAt: entry.createdAt.toISOString(),
    updatedAt: entry.updatedAt.toISOString(),
    reviewedAt: entry.reviewedAt ? entry.reviewedAt.toISOString() : null,
    author: entry.author,
    updatedBy: entry.updatedBy,
    reviewer: entry.reviewer,
    reviewNotes: entry.reviewNotes ?? null,
  }));

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <PageHeader
        eyebrow="Admin"
        title="Operations and governance"
        description="Monitor escalation volume, tune retrieval quality, and manage access policies."
      />

      <section className="grid gap-6 md:grid-cols-2">
        {panels.map((panel) => {
          const IconComponent = panel.icon;
          return (
            <article key={panel.title} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
                <IconComponent className="h-5 w-5" aria-hidden="true" />
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
          );
        })}
      </section>

      <GlossaryAdminPanel initialEntries={glossaryEntries} />
    </div>
  );
}

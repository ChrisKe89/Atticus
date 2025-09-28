import type { Metadata } from "next";
import Link from "next/link";
import { Calendar, FileText, KanbanSquare, Layers } from "lucide-react";
import { PageHeader } from "@/components/page-header";

const integrations = [
  {
    name: "Prisma ingestion",
    description:
      "Sync product sheets, tables, and field notes from Postgres with deterministic chunking.",
    icon: Layers,
    href: "#prisma",
  },
  {
    name: "Salesforce service cloud",
    description:
      "Escalate chat transcripts to a case queue with the full retrieval trace and request ID.",
    icon: KanbanSquare,
    href: "#salesforce",
  },
  {
    name: "SharePoint content feeds",
    description: "Monitor document libraries for updates and trigger incremental embeddings.",
    icon: FileText,
    href: "#sharepoint",
  },
  {
    name: "Teams meeting sync",
    description: "Push escalations and release notes to your customer success Teams channel.",
    icon: Calendar,
    href: "#teams",
  },
];

export const metadata: Metadata = {
  title: "Apps · Atticus",
};

export default function AppsPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <PageHeader
        eyebrow="Apps"
        title="Integrate Atticus across your stack"
        description="Connect ingest pipelines, escalation workflows, and downstream analytics in a few clicks."
      />

      <section className="grid gap-6 md:grid-cols-2">
        {integrations.map((integration) => (
          <article
            key={integration.name}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-300">
              <integration.icon className="h-5 w-5" aria-hidden="true" />
            </div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              {integration.name}
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              {integration.description}
            </p>
            <Link
              href={integration.href}
              className="mt-4 inline-flex items-center text-sm font-semibold text-indigo-600 hover:text-indigo-500"
            >
              View setup guide
            </Link>
          </article>
        ))}
      </section>
    </div>
  );
}

import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { GlossaryStatus, Prisma, Role } from "@prisma/client";
import { PageHeader } from "@/components/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { withRlsContext } from "@/lib/rls";
import { AdminOpsConsole, TicketSummary, UncertainChat } from "@/components/admin/admin-ops-console";
import type { GlossaryEntryDto } from "@/components/glossary/admin-panel";
import { getRequestContext } from "@/lib/request-context";

export const metadata: Metadata = {
  title: "Admin - Atticus",
};

type GlossaryEntryRecord = {
  id: string;
  term: string;
  definition: string;
  synonyms: string[];
  aliases: string[];
  units: string[];
  productFamilies: string[];
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
  const { user } = getRequestContext();
  if (user.role !== Role.ADMIN && user.role !== Role.REVIEWER) {
    redirect("/");
  }

  const { chats, tickets, glossary } = await withRlsContext(user, async (tx) => {
    const [pendingChats, ticketRows, glossaryRows] = await Promise.all([
      tx.chat.findMany({
        where: { status: "pending_review" },
        include: {
          author: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
          tickets: {
            select: { id: true, key: true, status: true, assignee: true, lastActivity: true },
          },
        },
        orderBy: { createdAt: "desc" },
      }),
      tx.ticket.findMany({
        orderBy: { updatedAt: "desc" },
        select: {
          id: true,
          key: true,
          status: true,
          assignee: true,
          lastActivity: true,
          summary: true,
        },
      }),
      tx.glossaryEntry.findMany({
        orderBy: { term: "asc" },
        include: {
          author: { select: { id: true, email: true, name: true } },
          updatedBy: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
        },
      }),
    ]);

    return { chats: pendingChats, tickets: ticketRows, glossary: glossaryRows };
  });

  const glossaryEntries: GlossaryEntryDto[] = (glossary as GlossaryEntryRecord[]).map((entry) => ({
    id: entry.id,
    term: entry.term,
    definition: entry.definition,
    synonyms: entry.synonyms,
    aliases: entry.aliases,
    units: entry.units,
    productFamilies: entry.productFamilies,
    status: entry.status,
    createdAt: entry.createdAt.toISOString(),
    updatedAt: entry.updatedAt.toISOString(),
    reviewedAt: entry.reviewedAt ? entry.reviewedAt.toISOString() : null,
    author: entry.author,
    updatedBy: entry.updatedBy,
    reviewer: entry.reviewer,
    reviewNotes: entry.reviewNotes ?? null,
  }));

  function parseSources(value: Prisma.JsonValue | null): UncertainChat["topSources"] {
    if (!Array.isArray(value)) {
      return [];
    }
    const sources: UncertainChat["topSources"] = [];
    for (const item of value) {
      if (typeof item !== "object" || item === null) {
        continue;
      }
      const path = "path" in item && typeof item.path === "string" ? item.path : null;
      if (!path) {
        continue;
      }
      sources.push({
        path,
        score: "score" in item && typeof item.score === "number" ? item.score : null,
        page: "page" in item && typeof item.page === "number" ? item.page : null,
        heading: "heading" in item && typeof item.heading === "string" ? item.heading : null,
        chunkId: "chunkId" in item && typeof item.chunkId === "string" ? item.chunkId : null,
      });
    }
    return sources;
  }

  function parseAuditLog(value: Prisma.JsonValue | null): Record<string, unknown>[] {
    if (!Array.isArray(value)) {
      return [];
    }
    const entries: Record<string, unknown>[] = [];
    for (const item of value) {
      if (typeof item === "object" && item !== null && !Array.isArray(item)) {
        entries.push(item as Record<string, unknown>);
      }
    }
    return entries;
  }

  const uncertainChats: UncertainChat[] = chats.map((chat) => ({
    id: chat.id,
    question: chat.question,
    answer: chat.answer ?? null,
    confidence: chat.confidence,
    status: chat.status,
    requestId: chat.requestId ?? null,
    createdAt: chat.createdAt.toISOString(),
    topSources: parseSources(chat.topSources),
    author: chat.author,
    reviewer: chat.reviewer,
    tickets: chat.tickets.map((ticket) => ({
      id: ticket.id,
      key: ticket.key,
      status: ticket.status,
      assignee: ticket.assignee,
      lastActivity: ticket.lastActivity ? ticket.lastActivity.toISOString() : null,
    })),
    followUpPrompt: chat.followUpPrompt ?? null,
    auditLog: parseAuditLog(chat.auditLog),
  }));

  const ticketSummaries: TicketSummary[] = tickets.map((ticket) => ({
    id: ticket.id,
    key: ticket.key,
    status: ticket.status,
    assignee: ticket.assignee,
    lastActivity: ticket.lastActivity ? ticket.lastActivity.toISOString() : null,
    summary: ticket.summary ?? null,
  }));

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <PageHeader
        eyebrow="Admin"
        title="Operations console"
        description="Review low-confidence chats, manage ticket escalations, and curate glossary terminology."
      />
      <AdminOpsConsole
        role={user.role}
        uncertain={uncertainChats}
        tickets={ticketSummaries}
        glossaryEntries={glossaryEntries}
      />
    </div>
  );
}

import { NextResponse } from "next/server";
import { Prisma } from "@prisma/client";
import { withRlsContext } from "@/lib/rls";
import { getRequestContext } from "@/lib/request-context";

const reviewableStatuses: string[] = ["pending_review", "draft", "rejected"];
type ReviewableChat = Prisma.ChatGetPayload<{
  include: {
    author: { select: { id: true; email: true; name: true } };
    reviewer: { select: { id: true; email: true; name: true } };
    tickets: { select: { id: true; key: true; status: true; assignee: true; lastActivity: true } };
  };
}>;

export async function GET() {
  const { user } = getRequestContext();
  const chats = await withRlsContext<ReviewableChat[]>(user, (tx) =>
    tx.chat.findMany({
      where: { status: { in: reviewableStatuses } },
      include: {
        author: { select: { id: true, email: true, name: true } },
        reviewer: { select: { id: true, email: true, name: true } },
        tickets: {
          select: {
            id: true,
            key: true,
            status: true,
            assignee: true,
            lastActivity: true,
          },
        },
      },
      orderBy: { createdAt: "desc" },
    })
  );

  const payload = chats.map((chat) => ({
    id: chat.id,
    question: chat.question,
    answer: chat.answer ?? null,
    confidence: chat.confidence,
    status: chat.status,
    createdAt: chat.createdAt.toISOString(),
    requestId: chat.requestId,
    topSources: normalizeSources(chat.topSources),
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
    auditLog: Array.isArray(chat.auditLog) ? chat.auditLog : [],
  }));

  return NextResponse.json(payload);
}

function normalizeSources(value: Prisma.JsonValue | null): Array<Record<string, unknown>> {
  if (!Array.isArray(value)) {
    return [];
  }
  const normalized: Array<Record<string, unknown>> = [];
  for (const item of value) {
    if (typeof item !== "object" || item === null) {
      continue;
    }
    const path = "path" in item && typeof item.path === "string" ? item.path : null;
    if (!path) {
      continue;
    }
    normalized.push({
      path,
      score: "score" in item && typeof item.score === "number" ? item.score : null,
      page: "page" in item && typeof item.page === "number" ? item.page : null,
      heading: "heading" in item && typeof item.heading === "string" ? item.heading : null,
      chunkId: "chunkId" in item && typeof item.chunkId === "string" ? item.chunkId : null,
    });
  }
  return normalized;
}


import { NextResponse } from "next/server";
import { Role } from "@prisma/client";
import { getServerAuthSession } from "@/lib/auth";
import { withRlsContext } from "@/lib/rls";

function canReview(role: Role | undefined): boolean {
  return role === Role.ADMIN || role === Role.REVIEWER;
}

export async function GET() {
  const session = await getServerAuthSession();
  if (!session) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!canReview(session.user.role)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  const chats = await withRlsContext(session, (tx) =>
    tx.chat.findMany({
      where: { status: "pending_review" },
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
    confidence: chat.confidence,
    status: chat.status,
    createdAt: chat.createdAt.toISOString(),
    requestId: chat.requestId,
    topSources: chat.topSources ?? [],
    author: chat.author,
    reviewer: chat.reviewer,
    tickets: chat.tickets.map((ticket) => ({
      id: ticket.id,
      key: ticket.key,
      status: ticket.status,
      assignee: ticket.assignee,
      lastActivity: ticket.lastActivity ? ticket.lastActivity.toISOString() : null,
    })),
  }));

  return NextResponse.json(payload);
}

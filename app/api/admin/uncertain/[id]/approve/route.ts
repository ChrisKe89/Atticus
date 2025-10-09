import { NextResponse } from "next/server";
import { Role } from "@prisma/client";
import { getServerAuthSession } from "@/lib/auth";
import { withRlsContext } from "@/lib/rls";

function canApprove(role: Role | undefined): boolean {
  return role === Role.ADMIN || role === Role.REVIEWER;
}

type ApproveBody = {
  notes?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const session = await getServerAuthSession();
  if (!session) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!canApprove(session.user.role)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  const { id } = params;
  let body: ApproveBody = {};
  try {
    body = (await request.json()) as ApproveBody;
  } catch (error) {
    body = {};
  }
  const notes = typeof body.notes === "string" ? body.notes.trim() : undefined;
  const eventTimestamp = new Date().toISOString();

  try {
    const result = await withRlsContext(session, async (tx) => {
      const existing = await tx.chat.findUnique({
        where: { id },
        select: { auditLog: true, status: true },
      });
      if (!existing) {
        return null;
      }
      if (existing.status !== "pending_review") {
        return "not_pending" as const;
      }

      const auditLog = Array.isArray(existing.auditLog) ? [...existing.auditLog] : [];
      auditLog.push({
        action: "approve",
        actorId: session.user.id,
        actorRole: session.user.role,
        at: eventTimestamp,
        notes: notes ?? null,
      });

      const updated = await tx.chat.update({
        where: { id },
        data: {
          status: "reviewed",
          reviewedAt: new Date(eventTimestamp),
          reviewedById: session.user.id,
          auditLog,
        },
        select: {
          id: true,
          status: true,
          reviewedAt: true,
          reviewer: { select: { id: true, email: true, name: true } },
          auditLog: true,
        },
      });

      return updated;
    });

    if (result === null) {
      return NextResponse.json({ error: "not_found" }, { status: 404 });
    }
    if (result === "not_pending") {
      return NextResponse.json({ error: "invalid_status" }, { status: 409 });
    }

    return NextResponse.json({
      id: result.id,
      status: result.status,
      reviewedAt: result.reviewedAt?.toISOString() ?? null,
      reviewer: result.reviewer,
      auditLog: result.auditLog ?? [],
    });
  } catch (error) {
    return NextResponse.json({ error: "server_error" }, { status: 500 });
  }
}

import { NextResponse } from "next/server";
import { Prisma } from "@prisma/client";
import { withRlsContext } from "@/lib/rls";
import { getRequestContext } from "@/lib/request-context";

type ApproveBody = {
  notes?: string;
  answer?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const { user } = getRequestContext();

  const { id } = params;
  let body: ApproveBody = {};
  try {
    body = (await request.json()) as ApproveBody;
  } catch (error) {
    body = {};
  }
  const notes = typeof body.notes === "string" ? body.notes.trim() : undefined;
  const editedAnswer = typeof body.answer === "string" ? body.answer.trim() : undefined;
  const eventTimestamp = new Date().toISOString();

  try {
    const result = await withRlsContext(user, async (tx) => {
      const existing = await tx.chat.findUnique({
        where: { id },
        select: { auditLog: true, status: true, orgId: true, requestId: true },
      });
      if (!existing) {
        return null;
      }
      if (existing.status !== "pending_review" && existing.status !== "draft") {
        return "not_pending" as const;
      }

      const auditLog: Prisma.JsonArray = Array.isArray(existing.auditLog)
        ? [...(existing.auditLog as Prisma.JsonArray)]
        : [];
      const logEntry: Prisma.JsonObject = {
        action: "approve",
        actorId: user.id,
        actorRole: null,
        at: eventTimestamp,
        notes: notes ?? null,
      };
      if (editedAnswer !== undefined) {
        logEntry.answerUpdated = editedAnswer.length > 0;
      }
      auditLog.push(logEntry);

      const updateData: Prisma.ChatUncheckedUpdateInput = {
        status: "reviewed",
        reviewedAt: new Date(eventTimestamp),
        reviewedById: user.id,
        auditLog,
      };

      if (editedAnswer !== undefined) {
        updateData.answer = editedAnswer;
      }

      const updated = await tx.chat.update({
        where: { id },
        data: updateData,
        select: {
          id: true,
          status: true,
          reviewedAt: true,
          reviewer: { select: { id: true, email: true, name: true } },
          auditLog: true,
          orgId: true,
          requestId: true,
        },
      });

      await tx.ragEvent.create({
        data: {
          orgId: existing.orgId,
          actorId: user.id,
          actorRole: null,
          action: "chat.approved",
          entity: "chat",
          chatId: updated.id,
          requestId: updated.requestId,
          after: {
            status: updated.status,
            reviewedAt: updated.reviewedAt?.toISOString() ?? null,
          },
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


import { NextResponse } from "next/server";
import { withRlsContext } from "@/lib/rls";
import { getRequestContext } from "@/lib/request-context";

type FollowUpBody = {
  prompt?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const { user } = getRequestContext();

  const { id } = params;
  let body: FollowUpBody;
  try {
    body = (await request.json()) as FollowUpBody;
  } catch (error) {
    body = {};
  }

  const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
  if (!prompt) {
    return NextResponse.json(
      { error: "invalid_request", detail: "Follow-up prompt is required." },
      { status: 400 }
    );
  }

  const timestamp = new Date().toISOString();

  const result = await withRlsContext(user, async (tx) => {
    const existing = await tx.chat.findUnique({
      where: { id },
      select: { id: true, status: true, auditLog: true, orgId: true },
    });
    if (!existing) {
      return null;
    }

    const auditLog = Array.isArray(existing.auditLog) ? [...existing.auditLog] : [];
    auditLog.push({
      action: "followup",
      at: timestamp,
      actorId: user.id,
      actorRole: null,
      prompt,
    });

    const updated = await tx.chat.update({
      where: { id },
      data: { followUpPrompt: prompt, auditLog },
      select: {
        id: true,
        followUpPrompt: true,
        auditLog: true,
        status: true,
        requestId: true,
      },
    });

    await tx.ragEvent.create({
      data: {
        orgId: existing.orgId,
        actorId: user.id,
        actorRole: null,
        action: "chat.followup_recorded",
        entity: "chat",
        chatId: updated.id,
        requestId: updated.requestId,
        after: {
          status: updated.status,
          followUpPrompt: updated.followUpPrompt,
        },
      },
    });

    return updated;
  });

  if (result === null) {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }

  return NextResponse.json({
    id: result.id,
    followUpPrompt: result.followUpPrompt,
    auditLog: result.auditLog ?? [],
  });
}


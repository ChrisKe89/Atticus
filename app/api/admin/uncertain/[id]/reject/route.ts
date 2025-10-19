import { withRlsContext } from "@/lib/rls";
import { getRequestContext } from "@/lib/request-context";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

type RejectBody = {
  notes?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveTraceIdentifiers(request);
  const { user } = getRequestContext();

  const { id } = params;
  let body: RejectBody = {};
  try {
    body = (await request.json()) as RejectBody;
  } catch {
    body = {};
  }

  const notes = typeof body.notes === "string" ? body.notes.trim() : undefined;
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
        return "not_reviewable" as const;
      }

      const auditLog = Array.isArray(existing.auditLog) ? [...existing.auditLog] : [];
      auditLog.push({
        action: "reject",
        actorId: user.id,
        actorRole: null,
        at: eventTimestamp,
        notes: notes ?? null,
      });

      const updated = await tx.chat.update({
        where: { id },
        data: {
          status: "rejected",
          auditLog,
        },
        select: {
          id: true,
          status: true,
          orgId: true,
          requestId: true,
          auditLog: true,
        },
      });

      await tx.ragEvent.create({
        data: {
          orgId: existing.orgId,
          actorId: user.id,
          actorRole: null,
          action: "chat.rejected",
          entity: "chat",
          chatId: updated.id,
          requestId: updated.requestId,
          after: {
            status: updated.status,
          },
        },
      });

      return updated;
    });

    if (result === null) {
      return jsonWithTrace({ error: "not_found" }, ids, { status: 404 });
    }
    if (result === "not_reviewable") {
      return jsonWithTrace({ error: "invalid_status" }, ids, { status: 409 });
    }

    return jsonWithTrace(
      {
        id: result.id,
        status: result.status,
        auditLog: result.auditLog ?? [],
      },
      ids,
    );
  } catch (error) {
    const detail = error instanceof Error ? error.message : undefined;
    return jsonWithTrace(
      { error: "server_error", detail: detail ?? "Failed to update chat status." },
      ids,
      { status: 500 },
    );
  }
}


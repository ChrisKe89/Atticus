import { Prisma, Role } from "@prisma/client";
import type { AskResponse } from "@/lib/ask-contract";
import { getServerAuthSession } from "@/lib/auth";
import { withRlsContext } from "@/lib/rls";

function parseConfidenceThreshold(): number {
  const raw = process.env.CONFIDENCE_THRESHOLD;
  if (!raw) {
    return 0.7;
  }
  const parsed = Number(raw);
  if (Number.isNaN(parsed) || parsed <= 0 || parsed > 1) {
    return 0.7;
  }
  return parsed;
}

function serializeSources(sources: AskResponse["sources"]): Prisma.JsonArray {
  return sources
    .map((source) => ({
      path: source.path,
      page: source.page ?? null,
      heading: source.heading ?? null,
      chunkId: source.chunkId ?? null,
      score: source.score ?? null,
    }))
    .filter((item) => item.path) as Prisma.JsonArray;
}

type CaptureArgs = {
  question: string;
  response: AskResponse;
};

export async function captureLowConfidenceChat({ question, response }: CaptureArgs): Promise<void> {
  const threshold = parseConfidenceThreshold();
  if (!response.should_escalate && response.confidence >= threshold) {
    return;
  }

  const session = await getServerAuthSession();
  if (!session?.user?.id || !session.user.orgId) {
    return;
  }

  try {
    await withRlsContext(session, async (tx) => {
      const now = new Date();
      const auditLog: Prisma.JsonArray = [
        {
          action: "captured",
          at: now.toISOString(),
          confidence: response.confidence,
          requestId: response.request_id,
        },
      ];

      const chat = await tx.chat.create({
        data: {
          orgId: session.user.orgId,
          userId: session.user.id,
          question,
          answer: response.answer,
          confidence: response.confidence,
          status: "pending_review",
          requestId: response.request_id,
          topSources: serializeSources(response.sources),
          auditLog,
        },
        select: { id: true },
      });

      await tx.ragEvent.create({
        data: {
          orgId: session.user.orgId,
          actorId: session.user.id,
          actorRole: session.user.role ?? Role.USER,
          action: "chat.captured",
          entity: "chat",
          chatId: chat.id,
          requestId: response.request_id,
          after: {
            status: "pending_review",
            confidence: response.confidence,
            requestId: response.request_id,
          },
        },
      });
    });
  } catch (error) {
    console.error("Failed to capture low-confidence chat", error);
  }
}

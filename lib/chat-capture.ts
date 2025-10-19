import { Prisma } from "@prisma/client";
import type { AskResponse } from "@/lib/ask-contract";
import { withRlsContext } from "@/lib/rls";
import type { RequestUser } from "@/lib/request-context";

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

function serializeSources(sources: AskResponse["sources"] | undefined): Prisma.JsonArray {
  return (sources ?? [])
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
  user: RequestUser | null | undefined;
};

export async function captureLowConfidenceChat({ question, response, user }: CaptureArgs): Promise<void> {
  if (response.clarification) {
    return;
  }

  const answers =
    response.answers && response.answers.length > 0
      ? response.answers
      : response.answer
        ? [
            {
              answer: response.answer,
              confidence: response.confidence ?? 0,
              should_escalate: response.should_escalate ?? false,
              model: undefined,
              family: undefined,
              family_label: undefined,
              sources: response.sources ?? [],
            },
          ]
        : [];

  if (answers.length === 0) {
    return;
  }

  const aggregatedConfidence =
    response.confidence ??
    (answers.length
      ? answers.reduce((acc, item) => Math.min(acc, item.confidence ?? 0), 1)
      : 0);
  const aggregatedEscalate =
    response.should_escalate ?? answers.some((item) => item.should_escalate);
  const aggregatedSources =
    response.sources && response.sources.length > 0
      ? response.sources
      : answers.flatMap((item) => item.sources ?? []);

  const aggregatedAnswer = answers
    .map((item) => {
      const metadata = [item.model, item.family_label ?? item.family].filter(Boolean).join(" · ");
      const heading = metadata ? `### ${metadata}\n\n` : "";
      return `${heading}${item.answer}`.trim();
    })
    .filter(Boolean)
    .join("\n\n");

  const threshold = parseConfidenceThreshold();
  if (!aggregatedEscalate && aggregatedConfidence >= threshold) {
    return;
  }

  if (!user?.id || !user.orgId) {
    return;
  }

  try {
    await withRlsContext(user, async (tx) => {
      const now = new Date();
      const auditLog: Prisma.JsonArray = [
        {
          action: "captured",
          at: now.toISOString(),
          confidence: aggregatedConfidence,
          requestId: response.request_id,
        },
      ];

      const chat = await tx.chat.create({
        data: {
          orgId: user.orgId,
          userId: user.id,
          question,
          answer: aggregatedAnswer,
          confidence: aggregatedConfidence,
          status: "pending_review",
          requestId: response.request_id,
          topSources: serializeSources(aggregatedSources),
          auditLog,
        },
        select: { id: true },
      });

      await tx.ragEvent.create({
        data: {
          orgId: user.orgId,
          actorId: user.id,
          actorRole: null,
          action: "chat.captured",
          entity: "chat",
          chatId: chat.id,
          requestId: response.request_id,
          after: {
            status: "pending_review",
            confidence: aggregatedConfidence,
            requestId: response.request_id,
          },
        },
      });
    });
  } catch (error) {
    const payload = {
      level: "error",
      event: "low_confidence_capture_failed",
      request_id: response.request_id,
      message: error instanceof Error ? error.message : "Unknown error",
      stack: error instanceof Error && error.stack ? error.stack : undefined,
    };
    console.error(JSON.stringify(payload));
  }
}


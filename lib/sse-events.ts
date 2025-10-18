import { z } from "zod";

import schema from "@/schemas/sse-events.schema.json";
import { askResponseSchema } from "@/lib/ask-contract";

const startEventSchema = z.object({
  type: z.literal("start"),
  requestId: z.string(),
});

const endEventSchema = z.object({
  type: z.literal("end"),
  requestId: z.string(),
});

const answerEventSchema = z.object({
  type: z.literal("answer"),
  payload: askResponseSchema,
});

export const sseEventSchema = z.union([startEventSchema, endEventSchema, answerEventSchema]);

export type SseStartEvent = z.infer<typeof startEventSchema>;
export type SseEndEvent = z.infer<typeof endEventSchema>;
export type SseAnswerEvent = z.infer<typeof answerEventSchema>;
export type AskStreamEvent = z.infer<typeof sseEventSchema>;

function assertSchemaParity() {
  if (!schema || !Array.isArray(schema.oneOf)) {
    return;
  }
  const definedTypes = new Set(schema.oneOf.map((entry) => entry?.properties?.type?.const));
  for (const literal of ["start", "end", "answer"]) {
    if (!definedTypes.has(literal)) {
      throw new Error(`SSE schema mismatch: missing ${literal} event in JSON schema`);
    }
  }
}

assertSchemaParity();

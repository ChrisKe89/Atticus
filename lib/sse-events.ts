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
  type SchemaEntry = {
    properties?: {
      type?: {
        const?: unknown;
      };
    };
    $ref?: unknown;
  };
  const definedTypes = new Set<string>();
  const entries = schema.oneOf as SchemaEntry[];
  for (const entry of entries) {
    const inlineConst = entry?.properties?.type?.const;
    const inlineType = typeof inlineConst === "string" ? (inlineConst as string) : undefined;
    if (inlineType && typeof inlineType === "string") {
      definedTypes.add(inlineType);
      continue;
    }
    const refValue = entry?.$ref;
    const ref = typeof refValue === "string" ? refValue : undefined;
    if (ref && typeof ref === "string") {
      const key = ref.split("/").pop();
      const collections =
        (schema.definitions as Record<string, SchemaEntry> | undefined) ??
        ((schema as { $defs?: Record<string, SchemaEntry> }).$defs ?? {});
      const node = key ? collections[key] : undefined;
      const refConst = node?.properties?.type?.const;
      const refType = typeof refConst === "string" ? (refConst as string) : undefined;
      if (refType) {
        definedTypes.add(refType);
      }
    }
  }
  for (const literal of ["start", "answer", "end"]) {
    if (!definedTypes.has(literal)) {
      throw new Error(`SSE schema mismatch: missing ${literal} event in JSON schema`);
    }
  }
}

assertSchemaParity();

import { z } from "zod";

const askSourceSchema = z.object({
  path: z.string(),
  page: z.number().int().nullable().optional(),
  heading: z.string().nullable().optional(),
  chunkId: z.string().nullable().optional(),
  score: z.number().nullable().optional(),
});

const clarificationOptionSchema = z.object({
  id: z.string(),
  label: z.string(),
});

const clarificationPayloadSchema = z.object({
  message: z.string(),
  options: z.array(clarificationOptionSchema),
});

const askAnswerSchema = z.object({
  answer: z.string(),
  confidence: z.number(),
  should_escalate: z.boolean(),
  model: z.string().nullable().optional(),
  family: z.string().nullable().optional(),
  family_label: z.string().nullable().optional(),
  sources: z.array(askSourceSchema),
});

export const askResponseSchema = z.object({
  answer: z.string().optional().nullable(),
  confidence: z.number().optional().nullable(),
  should_escalate: z.boolean().optional().nullable(),
  request_id: z.string(),
  sources: z.array(askSourceSchema).optional(),
  answers: z.array(askAnswerSchema).optional(),
  clarification: clarificationPayloadSchema.optional(),
});

export const askRequestSchema = z.object({
  question: z.string().trim().min(1, "question is required"),
  filters: z
    .record(z.string(), z.unknown())
    .nullish()
    .transform((value) => (value ? Object.fromEntries(Object.entries(value)) : undefined)),
  contextHints: z
    .array(z.string().min(1))
    .nullish()
    .transform((value) => value ?? undefined),
  topK: z
    .number()
    .int()
    .min(1)
    .max(32)
    .nullish()
    .transform((value) => value ?? undefined),
  models: z
    .array(z.string().min(1))
    .nullish()
    .transform((value) => (value && value.length ? value : undefined)),
});

export type AskResponse = z.infer<typeof askResponseSchema>;
export type AskRequest = z.infer<typeof askRequestSchema>;
export type AskSource = z.infer<typeof askSourceSchema>;
export type AskAnswer = z.infer<typeof askAnswerSchema>;
export type ClarificationPayload = z.infer<typeof clarificationPayloadSchema>;

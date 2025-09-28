import { z } from 'zod';

const askSourceSchema = z.object({
  path: z.string(),
  page: z.number().int().nullable().optional(),
  heading: z.string().nullable().optional(),
  chunkId: z.string().nullable().optional(),
  score: z.number().nullable().optional(),
});

export const askResponseSchema = z.object({
  answer: z.string(),
  confidence: z.number(),
  should_escalate: z.boolean(),
  request_id: z.string(),
  sources: z.array(askSourceSchema),
});

export const askRequestSchema = z.object({
  question: z.string().trim().min(1, 'question is required'),
  filters: z.record(z.string()).nullish().transform((value) => value ?? undefined),
  contextHints: z.array(z.string().min(1)).nullish().transform((value) => value ?? undefined),
  topK: z
    .number()
    .int()
    .min(1)
    .max(32)
    .nullish()
    .transform((value) => value ?? undefined),
});

export type AskResponse = z.infer<typeof askResponseSchema>;
export type AskRequest = z.infer<typeof askRequestSchema>;
export type AskSource = z.infer<typeof askSourceSchema>;

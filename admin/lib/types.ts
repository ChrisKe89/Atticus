export type SourceSummary = {
  path: string;
  score: number | null;
  page: number | null;
  heading: string | null;
  chunkId: string | null;
};

export type ReviewChat = {
  id: string;
  question: string;
  answer: string | null;
  confidence: number;
  status: string;
  requestId: string | null;
  createdAt: string;
  topSources: SourceSummary[];
  auditLog: Array<Record<string, unknown>> | null;
};

export type GlossaryEntry = {
  term: string;
  synonyms: string[];
  aliases: string[];
  units: string[];
  productFamilies: string[];
};

export type EvalSeed = {
  question: string;
  relevantDocuments: string[];
  expectedAnswer: string | null;
  notes: string | null;
};

export type ContentEntry = {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number;
  modified: string;
};

export type MetricsHistogramBucket = {
  bucket: string;
  count: number;
};

export type MetricsDashboard = {
  queries: number;
  avg_confidence: number;
  escalations: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  histogram: MetricsHistogramBucket[];
  recent_trace_ids: string[];
  rate_limit: Record<string, number> | null;
};

import { randomUUID } from "node:crypto";

import type {
  ContentEntry,
  EvalSeed,
  GlossaryEntry,
  MetricsDashboard,
  ReviewChat,
} from "./types";
import { buildUpstreamHeaders, getAtticusBaseUrl } from "./config";

function mergeHeaders(base: Headers, extra?: HeadersInit): Headers {
  if (!extra) {
    return base;
  }
  const merged = new Headers(base);
  const temp = new Headers(extra);
  temp.forEach((value, key) => merged.set(key, value));
  return merged;
}

export async function atticusFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const target = path.startsWith("/") ? path : `/${path}`;
  const headers = mergeHeaders(buildUpstreamHeaders(), init.headers);
  return fetch(`${getAtticusBaseUrl()}${target}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export function resolveRequestIds(source?: { headers: Headers | HeadersInit }): { requestId: string; traceId: string } {
  const base = randomUUID();
  if (!source) {
    return { requestId: base, traceId: base };
  }
  const headerBag = source.headers instanceof Headers ? source.headers : new Headers(source.headers);
  const requestId = headerBag.get("x-request-id") ?? base;
  const traceId = headerBag.get("x-trace-id") ?? requestId;
  return { requestId, traceId };
}

export function extractTraceHeaders(
  response: Response,
  fallback?: { requestId?: string; traceId?: string }
): Record<string, string> {
  const fallbackRequestId = fallback?.requestId ?? randomUUID();
  const requestId = response.headers.get("x-request-id") ?? fallbackRequestId;
  const fallbackTrace = fallback?.traceId ?? requestId;
  const traceId = response.headers.get("x-trace-id") ?? fallbackTrace;
  return {
    "X-Request-ID": requestId,
    "X-Trace-ID": traceId,
  };
}

export async function fetchReviewQueue(): Promise<ReviewChat[]> {
  const response = await atticusFetch("/api/admin/uncertain");
  if (!response.ok) {
    throw new Error(`Upstream returned ${response.status} while loading review queue.`);
  }
  const data = (await response.json()) as unknown;
  if (!Array.isArray(data)) {
    throw new Error("Unexpected response when loading review queue.");
  }
  return data as ReviewChat[];
}

export async function fetchGlossaryEntries(): Promise<GlossaryEntry[]> {
  const response = await atticusFetch("/api/admin/dictionary");
  if (!response.ok) {
    throw new Error(`Failed to load glossary entries (status ${response.status}).`);
  }
  const payload = (await response.json()) as unknown;
  const entries =
    payload && typeof payload === "object" && Array.isArray((payload as { entries?: unknown }).entries)
      ? ((payload as { entries: GlossaryEntry[] }).entries ?? [])
      : [];
  return entries.map((entry) => ({
    definition: typeof (entry as { definition?: unknown }).definition === "string"
      ? ((entry as { definition: string }).definition ?? "")
      : "",
    term: entry.term,
    synonyms: Array.isArray(entry.synonyms) ? entry.synonyms : [],
    aliases: Array.isArray(entry.aliases) ? entry.aliases : [],
    units: Array.isArray(entry.units) ? entry.units : [],
    productFamilies: Array.isArray((entry as { productFamilies?: unknown }).productFamilies)
      ? ((entry as { productFamilies: string[] }).productFamilies ?? [])
      : [],
    status:
      typeof (entry as { status?: unknown }).status === "string"
        ? ((entry as { status: string }).status ?? "PENDING")
        : "PENDING",
    reviewNotes:
      typeof (entry as { reviewNotes?: unknown }).reviewNotes === "string"
        ? ((entry as { reviewNotes: string }).reviewNotes ?? null)
        : null,
  }));
}

export async function fetchEvalSeeds(): Promise<EvalSeed[]> {
  const response = await atticusFetch("/api/admin/eval-seeds");
  if (!response.ok) {
    throw new Error(`Failed to load evaluation seeds (status ${response.status}).`);
  }
  const payload = (await response.json()) as unknown;
  if (payload && typeof payload === "object" && Array.isArray((payload as { seeds?: unknown }).seeds)) {
    return (payload as { seeds: Array<Record<string, unknown>> }).seeds.map((seed, index) => {
      const relevantDocuments = Array.isArray(seed.relevantDocuments)
        ? (seed.relevantDocuments as unknown[])
        : Array.isArray((seed as { relevant_documents?: unknown[] }).relevant_documents)
        ? (seed as { relevant_documents?: unknown[] }).relevant_documents ?? []
        : [];
      const expectedAnswerRaw =
        typeof seed.expectedAnswer === "string"
          ? seed.expectedAnswer
          : typeof (seed as { expected_answer?: unknown }).expected_answer === "string"
          ? (seed as { expected_answer?: string }).expected_answer ?? null
          : null;
      const expectedAnswer =
        typeof expectedAnswerRaw === "string" && expectedAnswerRaw.trim().length > 0
          ? expectedAnswerRaw.trim()
          : null;
      const notesRaw =
        typeof seed.notes === "string"
          ? seed.notes
          : typeof (seed as { notes?: unknown }).notes === "string"
          ? (seed as { notes?: string }).notes ?? null
          : null;
      const notes =
        typeof notesRaw === "string" && notesRaw.trim().length > 0 ? notesRaw.trim() : null;
      return {
        question: typeof seed.question === "string" ? seed.question : `Seed ${index + 1}`,
        relevantDocuments: relevantDocuments
          .map((item) => String(item).trim())
          .filter((value) => value.length > 0),
        expectedAnswer,
        notes,
      } satisfies EvalSeed;
    });
  }
  return [];
}

export async function fetchContentEntries(path = "."): Promise<ContentEntry[]> {
  const targetPath = path && path.trim().length > 0 ? path.trim() : ".";
  const response = await atticusFetch(`/api/admin/content/list?path=${encodeURIComponent(targetPath)}`);
  if (!response.ok) {
    throw new Error(`Failed to list content (status ${response.status}).`);
  }
  const payload = (await response.json()) as { entries?: Array<Record<string, unknown>> };
  const entries = Array.isArray(payload.entries) ? payload.entries : [];
  return entries
    .map((entry) => {
      const name = typeof entry.name === "string" ? entry.name : "";
      const entryPath = typeof entry.path === "string" ? entry.path : "";
      if (!name || !entryPath) {
        return null;
      }
      const type: ContentEntry["type"] = entry.type === "directory" ? "directory" : "file";
      const size = typeof entry.size === "number" && Number.isFinite(entry.size) ? entry.size : 0;
      const modified =
        typeof entry.modified === "string" && entry.modified.trim().length > 0
          ? entry.modified
          : new Date().toISOString();
      return {
        name,
        path: entryPath,
        type,
        size,
        modified,
      } satisfies ContentEntry;
    })
    .filter((value): value is ContentEntry => value !== null);
}

export async function fetchMetricsDashboard(): Promise<MetricsDashboard | null> {
  const response = await atticusFetch("/api/admin/metrics");
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json().catch(() => null)) as Partial<MetricsDashboard> | null;
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const histogramSource = Array.isArray(payload.histogram) ? payload.histogram : [];
  const histogram = histogramSource
    .map((item) => {
      if (!item || typeof item !== "object") {
        return null;
      }
      const bucket = "bucket" in item && typeof item.bucket === "string" ? item.bucket : String(item.bucket ?? "");
      const count = Number.isFinite((item as { count?: unknown }).count)
        ? Number((item as { count?: unknown }).count)
        : 0;
      return { bucket, count };
    })
    .filter((value): value is MetricsDashboard["histogram"][number] => value !== null);

  const recentIds = Array.isArray(payload.recent_trace_ids)
    ? payload.recent_trace_ids.map((item) => String(item))
    : [];

  const rateLimit =
    payload.rate_limit && typeof payload.rate_limit === "object" && !Array.isArray(payload.rate_limit)
      ? Object.fromEntries(
          Object.entries(payload.rate_limit).map(([key, value]) => [key, Number(value) || 0])
        )
      : null;

  return {
    queries: Number(payload.queries) || 0,
    avg_confidence: Number(payload.avg_confidence) || 0,
    escalations: Number(payload.escalations) || 0,
    avg_latency_ms: Number(payload.avg_latency_ms) || 0,
    p95_latency_ms: Number(payload.p95_latency_ms) || 0,
    histogram,
    recent_trace_ids: recentIds,
    rate_limit: rateLimit,
  };
}


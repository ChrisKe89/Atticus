import type { EvalSeed, GlossaryEntry, ReviewChat } from "./types";
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

export async function atticusFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const target = path.startsWith("/") ? path : `/${path}`;
  const headers = mergeHeaders(buildUpstreamHeaders(), init.headers);
  return fetch(`${getAtticusBaseUrl()}${target}`, {
    ...init,
    headers,
    cache: "no-store",
  });
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
    term: entry.term,
    synonyms: Array.isArray(entry.synonyms) ? entry.synonyms : [],
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

import { GlossaryStatus, Prisma } from "@prisma/client";
import {
  type TraceIdentifiers,
  jsonWithTrace,
  resolveTraceIdentifiers,
} from "@/lib/trace-headers";

function normalizeToken(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/gi, "")
    .toLowerCase();
}

function normalizeFamily(value: string): string {
  return value
    .trim()
    .replace(/[\s_-]+/g, " ")
    .replace(/\s+/g, " ")
    .toUpperCase();
}

function buildError(
  status: number,
  ids: TraceIdentifiers,
  error: string,
  detail: string,
  fields?: Record<string, string>,
) {
  const payload: Record<string, unknown> = {
    error,
    detail,
    request_id: ids.requestId,
    trace_id: ids.traceId,
  };
  if (fields) {
    payload.fields = fields;
  }
  return jsonWithTrace(payload, ids, { status });
}

export function parseStatus(value: unknown): GlossaryStatus {
  if (value === undefined || value === null || value === "") {
    return GlossaryStatus.PENDING;
  }
  if (typeof value !== "string") {
    throw new Error("Invalid status type");
  }
  const upper = value.toUpperCase();
  if (!(upper in GlossaryStatus)) {
    throw new Error("Unknown glossary status");
  }
  return GlossaryStatus[upper as keyof typeof GlossaryStatus];
}

export function parseSynonyms(value: unknown): string[] {
  return parseStringList(value);
}

function parseStringList(value: unknown): string[] {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter((item) => item.length > 0);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }
  throw new Error("Invalid list payload");
}

export function parseAliases(value: unknown): string[] {
  return parseStringList(value);
}

export function parseUnits(value: unknown): string[] {
  return parseStringList(value);
}

export function parseProductFamilies(value: unknown): { raw: string[]; normalized: string[] } {
  const families = parseStringList(value);
  const normalized = families.map(normalizeFamily).filter((item) => item.length > 0);
  return { raw: families, normalized: Array.from(new Set(normalized)) };
}

export function buildNormalizedAliases(term: string, synonyms: string[], aliases: string[]): string[] {
  const tokens = new Set<string>();
  [term, ...synonyms, ...aliases].forEach((value) => {
    const normalized = normalizeToken(value);
    if (normalized) {
      tokens.add(normalized);
    }
  });
  return Array.from(tokens);
}

export function serializeEntry(entry: any) {
  return {
    id: entry.id,
    term: entry.term,
    definition: entry.definition,
    synonyms: Array.isArray(entry.synonyms) ? entry.synonyms : [],
    aliases: Array.isArray(entry.aliases) ? entry.aliases : [],
    units: Array.isArray(entry.units) ? entry.units : [],
    productFamilies: Array.isArray(entry.productFamilies) ? entry.productFamilies : [],
    status: entry.status,
    createdAt: entry.createdAt.toISOString(),
    updatedAt: entry.updatedAt.toISOString(),
    reviewedAt: entry.reviewedAt ? entry.reviewedAt.toISOString() : null,
    author: entry.author
      ? {
          id: entry.author.id,
          email: entry.author.email,
          name: entry.author.name,
        }
      : null,
    updatedBy: entry.updatedBy
      ? {
          id: entry.updatedBy.id,
          email: entry.updatedBy.email,
          name: entry.updatedBy.name,
        }
      : null,
    reviewer: entry.reviewer
      ? {
          id: entry.reviewer.id,
          email: entry.reviewer.email,
          name: entry.reviewer.name,
        }
      : null,
    reviewNotes: entry.reviewNotes ?? null,
  };
}

export function snapshotEntry(entry: any) {
  return {
    term: entry.term,
    definition: entry.definition,
    synonyms: Array.isArray(entry.synonyms) ? entry.synonyms : [],
    aliases: Array.isArray(entry.aliases) ? entry.aliases : [],
    units: Array.isArray(entry.units) ? entry.units : [],
    productFamilies: Array.isArray(entry.productFamilies) ? entry.productFamilies : [],
    status: entry.status,
    reviewNotes: entry.reviewNotes ?? null,
  };
}

export function handleGlossaryError(
  error: unknown,
  source?: Parameters<typeof resolveTraceIdentifiers>[0] | TraceIdentifiers,
) {
  const ids =
    source && typeof source === "object" && "requestId" in source && "traceId" in source
      ? (source as TraceIdentifiers)
      : resolveTraceIdentifiers(source);
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
    return buildError(409, ids, "conflict", "Term already exists for this organization.");
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2025") {
    return buildError(404, ids, "not_found", "Glossary entry not found.");
  }
  if (error instanceof Error && error.message?.toLowerCase().includes("status")) {
    return buildError(400, ids, "invalid_request", error.message);
  }
  return buildError(500, ids, "internal_error", "An internal error occurred while processing the glossary request.");
}


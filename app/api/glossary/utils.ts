import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import { GlossaryStatus, Prisma } from "@prisma/client";
import { ForbiddenError, UnauthorizedError } from "@/lib/rbac";

function buildError(
  status: number,
  error: string,
  detail: string,
  fields?: Record<string, string>
) {
  const requestId = randomUUID();
  const payload: Record<string, unknown> = {
    error,
    detail,
    request_id: requestId,
  };
  if (fields) {
    payload.fields = fields;
  }
  const response = NextResponse.json(payload, { status });
  response.headers.set("X-Request-ID", requestId);
  return response;
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
  throw new Error("Invalid synonyms payload");
}

export function serializeEntry(entry: any) {
  return {
    id: entry.id,
    term: entry.term,
    definition: entry.definition,
    synonyms: Array.isArray(entry.synonyms) ? entry.synonyms : [],
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

export function handleGlossaryError(error: unknown) {
  if (error instanceof UnauthorizedError) {
    return buildError(401, "unauthorized", error.message || "Authentication required.");
  }
  if (error instanceof ForbiddenError) {
    return buildError(403, "forbidden", error.message || "Forbidden");
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
    return buildError(409, "conflict", "Term already exists for this organization.");
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2025") {
    return buildError(404, "not_found", "Glossary entry not found.");
  }
  if (error instanceof Error && error.message?.toLowerCase().includes("status")) {
    return buildError(400, "invalid_request", error.message);
  }
  return buildError(500, "internal_error", "An internal error occurred.");
}

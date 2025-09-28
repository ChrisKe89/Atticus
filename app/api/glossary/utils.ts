import { NextResponse } from "next/server";
import { GlossaryStatus, Prisma } from "@prisma/client";
import { ForbiddenError, UnauthorizedError } from "@/lib/rbac";

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
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
  if (error instanceof ForbiddenError) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2002") {
    return NextResponse.json(
      { error: "conflict", detail: "Term already exists for this organization." },
      { status: 409 }
    );
  }
  if (error instanceof Prisma.PrismaClientKnownRequestError && error.code === "P2025") {
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  }
  if (error instanceof Error && error.message?.toLowerCase().includes("status")) {
    return NextResponse.json({ error: "invalid_request", detail: error.message }, { status: 400 });
  }
  return NextResponse.json({ error: "internal_error" }, { status: 500 });
}

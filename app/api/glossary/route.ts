import type { NextRequest } from "next/server";
import { GlossaryStatus, Prisma } from "@prisma/client";
import { withRlsContext } from "@/lib/rls";
import {
  handleGlossaryError,
  parseAliases,
  parseProductFamilies,
  parseStatus,
  parseSynonyms,
  parseUnits,
  buildNormalizedAliases,
  serializeEntry,
  snapshotEntry,
} from "@/app/api/glossary/utils";
import { getRequestContext } from "@/lib/request-context";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

const relationSelect = {
  author: { select: { id: true, email: true, name: true } },
  updatedBy: { select: { id: true, email: true, name: true } },
  reviewer: { select: { id: true, email: true, name: true } },
} as const;

export async function GET(request: NextRequest) {
  const ids = resolveTraceIdentifiers(request);
  try {
    const { user } = getRequestContext();
    const entries = (await withRlsContext(user, (tx) =>
      tx.glossaryEntry.findMany({
        orderBy: { term: "asc" },
        include: {
          author: { select: { id: true, email: true, name: true } },
          updatedBy: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
        },
      } as any)
    )) as unknown[];
    return jsonWithTrace(entries.map(serializeEntry), ids);
  } catch (error) {
    return handleGlossaryError(error, ids);
  }
}

export async function POST(request: NextRequest) {
  const ids = resolveTraceIdentifiers(request);
  try {
    const { user } = getRequestContext();
    const payload = await request.json();
    const term = typeof payload.term === "string" ? payload.term.trim() : "";
    const definition = typeof payload.definition === "string" ? payload.definition.trim() : "";
    const synonyms = parseSynonyms(payload.synonyms);
    const aliases = parseAliases(payload.aliases);
    const units = parseUnits(payload.units);
    const families = parseProductFamilies(payload.productFamilies);
    if (!term || !definition) {
      return jsonWithTrace(
        { error: "invalid_request", detail: "Both term and definition are required." },
        ids,
        { status: 400 },
      );
    }

    const status = parseStatus(payload.status);
    const reviewNotes =
      typeof payload.reviewNotes === "string"
        ? payload.reviewNotes.trim() || null
        : payload.reviewNotes === null
        ? null
        : undefined;

    const result = await withRlsContext(user, async (tx) => {
      const existing = await tx.glossaryEntry.findFirst({
        where: { orgId: user.orgId, term },
      });

      const data: Record<string, unknown> = {
        definition,
        synonyms,
        aliases,
        units,
        productFamilies: families.raw,
        normalizedAliases: buildNormalizedAliases(term, synonyms, aliases),
        normalizedFamilies: families.normalized,
        status,
        updatedById: user.id,
      };
      if (reviewNotes !== undefined) {
        data.reviewNotes = reviewNotes;
      }
      if (status === GlossaryStatus.PENDING) {
        data.reviewedAt = null;
        data.reviewerId = null;
      } else {
        data.reviewedAt = new Date();
        data.reviewerId = user.id;
      }

      const entry = await tx.glossaryEntry.upsert({
        where: { orgId_term: { orgId: user.orgId, term } },
        create: {
          term,
          definition,
          synonyms,
          aliases,
          units,
          productFamilies: families.raw,
          normalizedAliases: buildNormalizedAliases(term, synonyms, aliases),
          normalizedFamilies: families.normalized,
          status,
          orgId: user.orgId,
          authorId: user.id,
          updatedById: user.id,
          reviewNotes: reviewNotes ?? null,
          reviewedAt: status === GlossaryStatus.PENDING ? null : new Date(),
          reviewerId: status === GlossaryStatus.PENDING ? null : user.id,
        },
        update: data,
        include: relationSelect,
      } as any);

      await tx.ragEvent.create({
        data: {
          orgId: user.orgId,
          actorId: user.id,
          actorRole: null,
          action: existing ? "glossary.updated" : "glossary.created",
          entity: "glossary",
          glossaryId: entry.id,
          before: existing ? snapshotEntry(existing) : Prisma.JsonNull,
          after: snapshotEntry(entry),
        },
      });

      return { entry, created: !existing };
    });

    return jsonWithTrace(serializeEntry(result.entry), ids, { status: result.created ? 201 : 200 });
  } catch (error) {
    return handleGlossaryError(error, ids);
  }
}



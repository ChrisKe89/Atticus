import { GlossaryStatus, Prisma } from "@prisma/client";
import { withRlsContext } from "@/lib/rls";
import {
  buildNormalizedAliases,
  parseAliases,
  parseProductFamilies,
  parseStatus,
  parseSynonyms,
  parseUnits,
  serializeEntry,
  handleGlossaryError,
  snapshotEntry,
} from "@/app/api/glossary/utils";
import { getRequestContext } from "@/lib/request-context";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

const relationSelect = {
  author: { select: { id: true, email: true, name: true } },
  updatedBy: { select: { id: true, email: true, name: true } },
  reviewer: { select: { id: true, email: true, name: true } },
} as const;

export async function PUT(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveTraceIdentifiers(request);
  try {
    const { user } = getRequestContext();
    const payload = await request.json();
    const definition = typeof payload.definition === "string" ? payload.definition.trim() : "";
    if (!definition) {
      return jsonWithTrace(
        { error: "invalid_request", detail: "Definition is required." },
        ids,
        { status: 400 },
      );
    }
    const term = typeof payload.term === "string" && payload.term.trim().length > 0 ? payload.term.trim() : undefined;
    const synonyms = parseSynonyms(payload.synonyms);
    const aliases = parseAliases(payload.aliases);
    const units = parseUnits(payload.units);
    const families = parseProductFamilies(payload.productFamilies);
    const status = parseStatus(payload.status);
    const reviewNotes =
      typeof payload.reviewNotes === "string"
        ? payload.reviewNotes.trim() || null
        : payload.reviewNotes === null
        ? null
        : undefined;

    const entry = await withRlsContext(user, async (tx) => {
      const existing = await tx.glossaryEntry.findUnique({
        where: { id: params.id },
        include: relationSelect,
      });
      if (!existing) {
        return null;
      }

      const before = snapshotEntry(existing);
      const data: Record<string, unknown> = {
        definition,
        synonyms,
        aliases,
        units,
        productFamilies: families.raw,
        normalizedAliases: buildNormalizedAliases(term ?? existing.term, synonyms, aliases),
        normalizedFamilies: families.normalized,
        status,
        updatedById: user.id,
      };
      if (term) {
        data.term = term;
      }
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

      const updated = await tx.glossaryEntry.update({
        where: { id: params.id },
        data,
        include: relationSelect,
      } as any);

      await tx.ragEvent.create({
        data: {
          orgId: user.orgId,
          actorId: user.id,
          actorRole: null,
          action: "glossary.updated",
          entity: "glossary",
          glossaryId: updated.id,
          before,
          after: snapshotEntry(updated),
        },
      });

      return updated;
    });

    if (!entry) {
      return jsonWithTrace({ error: "not_found" }, ids, { status: 404 });
    }

    return jsonWithTrace(serializeEntry(entry), ids);
  } catch (error) {
    return handleGlossaryError(error, ids);
  }
}

export async function PATCH(request: Request, ctx: { params: { id: string } }) {
  return PUT(request, ctx);
}

export async function DELETE(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveTraceIdentifiers(request);
  try {
    const { user } = getRequestContext();
    const result = await withRlsContext(user, async (tx) => {
      const existing = await tx.glossaryEntry.findUnique({ where: { id: params.id } });
      if (!existing) {
        return null;
      }
      await tx.glossaryEntry.delete({ where: { id: params.id } });
      await tx.ragEvent.create({
        data: {
          orgId: user.orgId,
          actorId: user.id,
          actorRole: null,
          action: "glossary.deleted",
          entity: "glossary",
          glossaryId: existing.id,
          before: snapshotEntry(existing),
          after: Prisma.JsonNull,
        },
      });
      return true;
    });
    if (result === null) {
      return jsonWithTrace({ error: "not_found" }, ids, { status: 404 });
    }
    return jsonWithTrace({ status: "ok" }, ids);
  } catch (error) {
    return handleGlossaryError(error, ids);
  }
}


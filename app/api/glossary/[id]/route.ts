import { NextResponse } from "next/server";
import { GlossaryStatus, Prisma } from "@prisma/client";
import { withRlsContext } from "@/lib/rls";
import { canEditGlossary } from "@/lib/rbac";
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

const relationSelect = {
  author: { select: { id: true, email: true, name: true } },
  updatedBy: { select: { id: true, email: true, name: true } },
  reviewer: { select: { id: true, email: true, name: true } },
} as const;

export async function PUT(request: Request, { params }: { params: { id: string } }) {
  try {
    const { user } = getRequestContext();
    const editor = canEditGlossary(user);
    const payload = await request.json();
    const definition = typeof payload.definition === "string" ? payload.definition.trim() : "";
    if (!definition) {
      return NextResponse.json(
        { error: "invalid_request", detail: "Definition is required." },
        { status: 400 }
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

    const entry = await withRlsContext(editor, async (tx) => {
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
        updatedById: editor.id,
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
        data.reviewerId = editor.id;
      }

      const updated = await tx.glossaryEntry.update({
        where: { id: params.id },
        data,
        include: relationSelect,
      } as any);

      await tx.ragEvent.create({
        data: {
          orgId: editor.orgId,
          actorId: editor.id,
          actorRole: editor.role,
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
      return NextResponse.json({ error: "not_found" }, { status: 404 });
    }

    return NextResponse.json(serializeEntry(entry));
  } catch (error) {
    return handleGlossaryError(error);
  }
}

export async function PATCH(request: Request, ctx: { params: { id: string } }) {
  return PUT(request, ctx);
}

export async function DELETE(_: Request, { params }: { params: { id: string } }) {
  try {
    const { user } = getRequestContext();
    const editor = canEditGlossary(user);
    const result = await withRlsContext(editor, async (tx) => {
      const existing = await tx.glossaryEntry.findUnique({ where: { id: params.id } });
      if (!existing) {
        return null;
      }
      await tx.glossaryEntry.delete({ where: { id: params.id } });
      await tx.ragEvent.create({
        data: {
          orgId: editor.orgId,
          actorId: editor.id,
          actorRole: editor.role,
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
      return NextResponse.json({ error: "not_found" }, { status: 404 });
    }
    return NextResponse.json({ status: "ok" });
  } catch (error) {
    return handleGlossaryError(error);
  }
}

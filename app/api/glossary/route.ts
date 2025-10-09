import { NextResponse } from "next/server";
import { GlossaryStatus, Prisma } from "@prisma/client";
import { getServerAuthSession } from "@/lib/auth";
import { withRlsContext } from "@/lib/rls";
import { canEditGlossary, canReviewGlossary } from "@/lib/rbac";
import {
  handleGlossaryError,
  parseStatus,
  parseSynonyms,
  serializeEntry,
  snapshotEntry,
} from "@/app/api/glossary/utils";

const relationSelect = {
  author: { select: { id: true, email: true, name: true } },
  updatedBy: { select: { id: true, email: true, name: true } },
  reviewer: { select: { id: true, email: true, name: true } },
} as const;

export async function GET() {
  try {
    const session = canReviewGlossary(await getServerAuthSession());
    const entries = (await withRlsContext(session, (tx) =>
      tx.glossaryEntry.findMany({
        orderBy: { term: "asc" },
        include: {
          author: { select: { id: true, email: true, name: true } },
          updatedBy: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
        },
      } as any)
    )) as unknown[];
    return NextResponse.json(entries.map(serializeEntry));
  } catch (error) {
    return handleGlossaryError(error);
  }
}

export async function POST(request: Request) {
  try {
    const session = canEditGlossary(await getServerAuthSession());
    const payload = await request.json();
    const term = typeof payload.term === "string" ? payload.term.trim() : "";
    const definition = typeof payload.definition === "string" ? payload.definition.trim() : "";
    const synonyms = parseSynonyms(payload.synonyms);
    if (!term || !definition) {
      return NextResponse.json(
        { error: "invalid_request", detail: "Both term and definition are required." },
        { status: 400 }
      );
    }

    const status = parseStatus(payload.status);
    const reviewNotes =
      typeof payload.reviewNotes === "string"
        ? payload.reviewNotes.trim() || null
        : payload.reviewNotes === null
        ? null
        : undefined;

    const result = await withRlsContext(session, async (tx) => {
      const existing = await tx.glossaryEntry.findFirst({
        where: { orgId: session.user.orgId, term },
      });

      const data: Record<string, unknown> = {
        definition,
        synonyms,
        status,
        updatedById: session.user.id,
      };
      if (reviewNotes !== undefined) {
        data.reviewNotes = reviewNotes;
      }
      if (status === GlossaryStatus.PENDING) {
        data.reviewedAt = null;
        data.reviewerId = null;
      } else {
        data.reviewedAt = new Date();
        data.reviewerId = session.user.id;
      }

      const entry = await tx.glossaryEntry.upsert({
        where: { orgId_term: { orgId: session.user.orgId, term } },
        create: {
          term,
          definition,
          synonyms,
          status,
          orgId: session.user.orgId,
          authorId: session.user.id,
          updatedById: session.user.id,
          reviewNotes: reviewNotes ?? null,
          reviewedAt: status === GlossaryStatus.PENDING ? null : new Date(),
          reviewerId: status === GlossaryStatus.PENDING ? null : session.user.id,
        },
        update: data,
        include: relationSelect,
      } as any);

      await tx.ragEvent.create({
        data: {
          orgId: session.user.orgId,
          actorId: session.user.id,
          actorRole: session.user.role,
          action: existing ? "glossary.updated" : "glossary.created",
          entity: "glossary",
          glossaryId: entry.id,
          before: existing ? snapshotEntry(existing) : Prisma.JsonNull,
          after: snapshotEntry(entry),
        },
      });

      return { entry, created: !existing };
    });

    return NextResponse.json(serializeEntry(result.entry), { status: result.created ? 201 : 200 });
  } catch (error) {
    return handleGlossaryError(error);
  }
}

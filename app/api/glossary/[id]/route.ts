import { NextResponse } from 'next/server';
import { GlossaryStatus } from '@prisma/client';
import { getServerAuthSession } from '@/lib/auth';
import { withRlsContext } from '@/lib/rls';
import { canEditGlossary } from '@/lib/rbac';
import { parseStatus, parseSynonyms, serializeEntry, handleGlossaryError } from '@/app/api/glossary/utils';

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  try {
    const session = canEditGlossary(await getServerAuthSession());
    const payload = await request.json();
    const updates: Record<string, unknown> = {};
    if (typeof payload.definition === 'string' && payload.definition.trim()) {
      updates.definition = payload.definition.trim();
    }
    if (payload.synonyms !== undefined) {
      updates.synonyms = parseSynonyms(payload.synonyms);
    }
    if (payload.reviewNotes !== undefined) {
      if (typeof payload.reviewNotes === 'string') {
        const note = payload.reviewNotes.trim();
        updates.reviewNotes = note ? note : null;
      } else if (payload.reviewNotes === null) {
        updates.reviewNotes = null;
      }
    }
    if (payload.status) {
      const status = parseStatus(payload.status);
      updates.status = status;
      if (status === GlossaryStatus.PENDING) {
        updates.reviewedAt = null;
        updates.reviewerId = null;
      } else {
        updates.reviewedAt = new Date();
        updates.reviewerId = session.user.id;
      }
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ error: 'invalid_request', detail: 'Provide definition or status.' }, { status: 400 });
    }

    const entry = await withRlsContext(session, (tx) =>
      tx.glossaryEntry.update({
        where: { id: params.id },
        data: {
          ...updates,
          updatedById: session.user.id,
        },
        include: {
          author: { select: { id: true, email: true, name: true } },
          updatedBy: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
        },
      })
    );

    return NextResponse.json(serializeEntry(entry));
  } catch (error) {
    return handleGlossaryError(error);
  }
}

export async function DELETE(_: Request, { params }: { params: { id: string } }) {
  try {
    const session = canEditGlossary(await getServerAuthSession());
    await withRlsContext(session, (tx) => tx.glossaryEntry.delete({ where: { id: params.id } }));
    return NextResponse.json({ status: 'ok' });
  } catch (error) {
    return handleGlossaryError(error);
  }
}

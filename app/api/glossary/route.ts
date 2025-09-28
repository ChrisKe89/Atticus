import { NextResponse } from 'next/server';
import { getServerAuthSession } from '@/lib/auth';
import { withRlsContext } from '@/lib/rls';
import { canEditGlossary, canReviewGlossary } from '@/lib/rbac';
import { handleGlossaryError, parseStatus, parseSynonyms, serializeEntry } from '@/app/api/glossary/utils';

export async function GET() {
  try {
    const session = canReviewGlossary(await getServerAuthSession());
    const entries = (await withRlsContext(session, (tx) =>
      tx.glossaryEntry.findMany({
        orderBy: { term: 'asc' },
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
    const term = typeof payload.term === 'string' ? payload.term.trim() : '';
    const definition = typeof payload.definition === 'string' ? payload.definition.trim() : '';
    const synonyms = parseSynonyms(payload.synonyms);
    if (!term || !definition) {
      return NextResponse.json(
        { error: 'invalid_request', detail: 'Both term and definition are required.' },
        { status: 400 }
      );
    }

    const status = parseStatus(payload.status);

    const entry = await withRlsContext(session, (tx) =>
      tx.glossaryEntry.create({
        data: {
          term,
          definition,
          synonyms,
          status,
          orgId: session.user.orgId,
          authorId: session.user.id,
          updatedById: session.user.id,
        },
        include: {
          author: { select: { id: true, email: true, name: true } },
          updatedBy: { select: { id: true, email: true, name: true } },
          reviewer: { select: { id: true, email: true, name: true } },
        },
      } as any)
    );

    return NextResponse.json(serializeEntry(entry), { status: 201 });
  } catch (error) {
    return handleGlossaryError(error);
  }
}

import { NextResponse } from 'next/server';
import { getServerAuthSession } from '@/lib/auth';
import { withRlsContext } from '@/lib/rls';
import { canEditGlossary } from '@/lib/rbac';
import { parseStatus, serializeEntry, handleGlossaryError } from '@/app/api/glossary/utils';

export async function PATCH(request: Request, { params }: { params: { id: string } }) {
  try {
    const session = canEditGlossary(await getServerAuthSession());
    const payload = await request.json();
    const updates: Record<string, unknown> = {};
    if (typeof payload.definition === 'string' && payload.definition.trim()) {
      updates.definition = payload.definition.trim();
    }
    if (payload.status) {
      updates.status = parseStatus(payload.status);
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

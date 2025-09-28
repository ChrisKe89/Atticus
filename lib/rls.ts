import type { Session } from 'next-auth';
import type { Prisma } from '@prisma/client';
import { prisma, setRlsContext, clearRlsContext } from '@/lib/prisma';

export async function withRlsContext<T>(
  session: Session | null,
  fn: (client: Prisma.TransactionClient) => Promise<T>
): Promise<T> {
  if (!session?.user?.id || !session.user.orgId || !session.user.role) {
    throw new Error('RBAC enforcement requires an authenticated session');
  }

  return prisma.$transaction(async (tx) => {
    await setRlsContext(tx, {
      userId: session.user.id,
      role: session.user.role,
      orgId: session.user.orgId,
    });

    try {
      return await fn(tx);
    } finally {
      await clearRlsContext(tx);
    }
  });
}

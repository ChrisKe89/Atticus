import type { Prisma } from "@prisma/client";
import { prisma, setRlsContext, clearRlsContext } from "@/lib/prisma";
import type { RequestUser } from "@/lib/request-context";

export async function withRlsContext<T>(
  user: RequestUser | null | undefined,
  fn: (client: Prisma.TransactionClient) => Promise<T>
): Promise<T> {
  if (!user?.id || !user.orgId) {
    throw new Error("User context with id and orgId is required for RLS.");
  }

  return prisma.$transaction(async (tx) => {
    await setRlsContext(tx, {
      userId: user.id,
      orgId: user.orgId,
    });

    try {
      return await fn(tx);
    } finally {
      await clearRlsContext(tx);
    }
  });
}

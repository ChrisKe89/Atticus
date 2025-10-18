import type { Prisma } from "@prisma/client";
import { prisma, setRlsContext, clearRlsContext } from "@/lib/prisma";
import type { RequestUser } from "@/lib/request-context";

export async function withRlsContext<T>(
  user: RequestUser | null | undefined,
  fn: (client: Prisma.TransactionClient) => Promise<T>
): Promise<T> {
  if (!user?.id || !user.orgId || !user.role) {
    throw new Error("RBAC enforcement requires an upstream user context.");
  }

  return prisma.$transaction(async (tx) => {
    await setRlsContext(tx, {
      userId: user.id,
      role: user.role,
      orgId: user.orgId,
    });

    try {
      return await fn(tx);
    } finally {
      await clearRlsContext(tx);
    }
  });
}

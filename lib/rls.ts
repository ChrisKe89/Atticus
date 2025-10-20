import { Prisma, Role } from "@prisma/client";
import { prisma, setRlsContext, clearRlsContext } from "@/lib/prisma";
import type { RequestUser } from "@/lib/request-context";

function normaliseEmail(user: RequestUser): string {
  if (user.email) {
    return user.email.toLowerCase();
  }
  const fallback = user.id.replace(/[^a-z0-9]+/gi, ".").replace(/\.\.+/g, ".").replace(/^\.+|\.+$/g, "");
  const localPart = fallback || "service";
  return `${localPart}@generated.atticus`;
}

function normaliseName(user: RequestUser): string {
  return user.name ?? user.email ?? user.id;
}

async function ensureRequestUser(
  tx: Prisma.TransactionClient,
  user: RequestUser,
): Promise<void> {
  const existing = await tx.user.findUnique({ where: { id: user.id } });
  if (existing) {
    return;
  }

  await tx.user.create({
    data: {
      id: user.id,
      email: normaliseEmail(user),
      name: normaliseName(user),
      role: Role.ADMIN,
      orgId: user.orgId,
    },
  });
}

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

    await ensureRequestUser(tx, user);

    try {
      return await fn(tx);
    } finally {
      try {
        await clearRlsContext(tx);
      } catch (error) {
        console.warn(
          JSON.stringify({
            level: "warn",
            event: "rls_clear_failed",
            message: error instanceof Error ? error.message : "Failed to clear RLS context",
          })
        );
      }
    }
  });
}

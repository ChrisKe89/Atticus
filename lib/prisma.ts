import { PrismaClient, Prisma } from "@prisma/client";

type GlobalWithPrisma = typeof globalThis & {
  prisma?: PrismaClient;
};

const globalForPrisma = globalThis as GlobalWithPrisma;

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["query", "error", "warn"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}

type PrismaContextClient = PrismaClient | Prisma.TransactionClient;

export async function setRlsContext(
  client: PrismaContextClient,
  options: { userId: string; role: string; orgId: string }
) {
  const { userId, role, orgId } = options;
  await client.$executeRaw`SELECT set_config('app.current_user_id', ${userId}, true)`;
  await client.$executeRaw`SELECT set_config('app.current_user_role', ${role}, true)`;
  await client.$executeRaw`SELECT set_config('app.current_org_id', ${orgId}, true)`;
}

export async function clearRlsContext(client: PrismaContextClient) {
  await client.$executeRaw`SELECT set_config('app.current_user_id', '', true)`;
  await client.$executeRaw`SELECT set_config('app.current_user_role', 'SERVICE', true)`;
  await client.$executeRaw`SELECT set_config('app.current_org_id', '', true)`;
}

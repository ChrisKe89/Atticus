import { PrismaClient, Role } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  const defaultOrgId = process.env.DEFAULT_ORG_ID ?? 'org-atticus';
  const defaultOrgName = process.env.DEFAULT_ORG_NAME ?? 'Atticus Default';
  const adminEmail = process.env.ADMIN_EMAIL;
  const adminName = process.env.ADMIN_NAME ?? 'Atticus Admin';

  const organization = await prisma.organization.upsert({
    where: { id: defaultOrgId },
    update: { name: defaultOrgName },
    create: {
      id: defaultOrgId,
      name: defaultOrgName,
    },
  });

  if (adminEmail) {
    await prisma.user.upsert({
      where: { email: adminEmail.toLowerCase() },
      update: {
        role: Role.ADMIN,
        orgId: organization.id,
      },
      create: {
        email: adminEmail.toLowerCase(),
        name: adminName,
        role: Role.ADMIN,
        orgId: organization.id,
      },
    });
  }
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error('Seeding failed', error);
    await prisma.$disconnect();
    process.exit(1);
  });

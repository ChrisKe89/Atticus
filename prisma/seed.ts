import { GlossaryStatus, PrismaClient, Role } from "@prisma/client";

const prisma = new PrismaClient();

type SeedUser = {
  id: string;
  email: string;
  name: string;
  role: Role;
};

type GlossarySeed = {
  id: string;
  term: string;
  definition: string;
  synonyms: string[];
  status: GlossaryStatus;
  reviewNotes?: string;
  reviewerId?: string;
  reviewedAt?: Date;
};

const seedUsers: SeedUser[] = [
  {
    id: "user-seed-author",
    email: "glossary.author@seed.atticus",
    name: "Glossary Seed Author",
    role: Role.REVIEWER,
  },
  {
    id: "user-seed-approver",
    email: "glossary.approver@seed.atticus",
    name: "Glossary Seed Approver",
    role: Role.ADMIN,
  },
];

async function main() {
  const defaultOrgId = process.env.DEFAULT_ORG_ID ?? "org-atticus";
  const defaultOrgName = process.env.DEFAULT_ORG_NAME ?? "Atticus Default";
  const adminEmail = process.env.ADMIN_EMAIL;
  const adminName = process.env.ADMIN_NAME ?? "Atticus Admin";

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

  const seededUsers = await Promise.all(
    seedUsers.map((user) =>
      prisma.user.upsert({
        where: { id: user.id },
        update: {
          email: user.email,
          name: user.name,
          role: user.role,
          orgId: organization.id,
        },
        create: {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
          orgId: organization.id,
        },
      })
    )
  );

  const author = seededUsers.find((user) => user.id === "user-seed-author");
  const approver = seededUsers.find((user) => user.id === "user-seed-approver");

  if (!author || !approver) {
    throw new Error("Failed to seed glossary users");
  }

  const glossarySeeds: GlossarySeed[] = [
    {
      id: "glossary-entry-managed-print-services",
      term: "Managed Print Services",
      definition:
        "End-to-end management of printers, consumables, maintenance, and support delivered as a subscription.",
      synonyms: ["MPS", "Print-as-a-service"],
      status: GlossaryStatus.APPROVED,
      reviewNotes: "Approved for launch collateral and onboarding playbooks.",
      reviewerId: approver.id,
      reviewedAt: new Date("2024-05-01T12:00:00Z"),
    },
    {
      id: "glossary-entry-proactive-maintenance",
      term: "Proactive Maintenance",
      definition:
        "Scheduled device inspections and firmware rollouts designed to prevent outages before they impact revenue teams.",
      synonyms: ["Preventative maintenance"],
      status: GlossaryStatus.PENDING,
    },
    {
      id: "glossary-entry-toner-optimization",
      term: "Toner Optimization",
      definition:
        "Adaptive print routing and toner yield tracking that reduce waste while maintaining SLA-compliant image quality.",
      synonyms: ["Smart toner", "Consumable optimisation"],
      status: GlossaryStatus.REJECTED,
      reviewNotes: "Rejected pending customer-ready evidence and usage data.",
      reviewerId: approver.id,
      reviewedAt: new Date("2024-05-15T09:30:00Z"),
    },
  ];

  await Promise.all(
    glossarySeeds.map((entry) =>
      prisma.glossaryEntry.upsert({
        where: { id: entry.id },
        update: {
          term: entry.term,
          definition: entry.definition,
          synonyms: entry.synonyms,
          status: entry.status,
          orgId: organization.id,
          authorId: author.id,
          reviewerId: entry.reviewerId ?? null,
          reviewNotes: entry.reviewNotes ?? null,
          reviewedAt: entry.reviewedAt ?? null,
        },
        create: {
          id: entry.id,
          term: entry.term,
          definition: entry.definition,
          synonyms: entry.synonyms,
          status: entry.status,
          orgId: organization.id,
          authorId: author.id,
          reviewerId: entry.reviewerId ?? null,
          reviewNotes: entry.reviewNotes ?? null,
          reviewedAt: entry.reviewedAt ?? null,
        },
      })
    )
  );
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error("Seeding failed", error);
    await prisma.$disconnect();
    process.exit(1);
  });

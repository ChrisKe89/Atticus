import { PrismaAdapter } from "@auth/prisma-adapter";
import type { Adapter, AdapterUser } from "next-auth/adapters";
import type { Session } from "next-auth";
import { getServerSession } from "next-auth/next";
import EmailProvider from "next-auth/providers/email";
import nodemailer from "nodemailer";
import fs from "node:fs/promises";
import path from "node:path";
import { Role } from "@prisma/client";
import { prisma } from "@/lib/prisma";

const defaultOrgId = process.env.DEFAULT_ORG_ID ?? "org-atticus";
const emailFrom = process.env.EMAIL_FROM ?? process.env.SMTP_FROM ?? "atticus@localhost";

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

async function persistMagicLink(email: string, url: string) {
  const mailboxDir = process.env.AUTH_DEBUG_MAILBOX_DIR;
  if (!mailboxDir) {
    return;
  }
  const targetDir = path.resolve(mailboxDir);
  await fs.mkdir(targetDir, { recursive: true });
  const filePath = path.join(targetDir, `${normalizeEmail(email)}.txt`);
  const payload = `${new Date().toISOString()}\n${url}\n`;
  await fs.writeFile(filePath, payload, { encoding: "utf-8" });
}

const baseAdapter = PrismaAdapter(prisma) as Adapter;

type CreateUserParams = Parameters<NonNullable<Adapter["createUser"]>>[0];
type UpdateUserParams = Parameters<NonNullable<Adapter["updateUser"]>>[0];
type NextAuthHandler = (typeof import("next-auth/next"))["default"];
type ExtractAuthOptions<T> = T extends (...args: [...infer _Rest, infer Options]) => any
  ? Options
  : never;
type NextAuthConfig = ExtractAuthOptions<NextAuthHandler>;
type AuthCallbacks = NonNullable<NextAuthConfig["callbacks"]>;
type JwtCallbackParams = Parameters<NonNullable<AuthCallbacks["jwt"]>>[0];
type SessionCallbackParams = Parameters<NonNullable<AuthCallbacks["session"]>>[0];
type SignInCallbackParams = Parameters<NonNullable<AuthCallbacks["signIn"]>>[0];
type AuthEvents = NonNullable<NextAuthConfig["events"]>;
type CreateUserEventParams = Parameters<NonNullable<AuthEvents["createUser"]>>[0];

const adapter: Adapter = {
  ...baseAdapter,
  async createUser(data: CreateUserParams) {
    const userData = data as AdapterUser & { role?: Role; orgId?: string };
    if (!userData.email) {
      throw new Error("Email is required to create a user");
    }
    const normalized = normalizeEmail(userData.email);
    const created = await prisma.user.create({
      data: {
        email: normalized,
        name: userData.name ?? null,
        image: userData.image ?? null,
        emailVerified: userData.emailVerified ?? null,
        role: userData.role ?? Role.USER,
        orgId: userData.orgId ?? defaultOrgId,
      },
    });
    return created as unknown as AdapterUser;
  },
  async updateUser(data: UpdateUserParams) {
    if (!data.id) {
      throw new Error("updateUser requires an id");
    }
    const normalizedEmail = data.email ? normalizeEmail(data.email) : undefined;
    const updated = await prisma.user.update({
      where: { id: data.id as string },
      data: {
        name: data.name ?? undefined,
        image: data.image ?? undefined,
        email: normalizedEmail ?? undefined,
        emailVerified: data.emailVerified ?? undefined,
        role: (data as AdapterUser & { role?: Role }).role ?? Role.USER,
        orgId: (data as AdapterUser & { orgId?: string }).orgId ?? defaultOrgId,
      },
    });
    return updated as unknown as AdapterUser;
  },
};

function buildEmailServer() {
  const host = process.env.EMAIL_SERVER_HOST ?? process.env.SMTP_HOST ?? "localhost";
  const port = Number(process.env.EMAIL_SERVER_PORT ?? process.env.SMTP_PORT ?? 587);
  const user = process.env.EMAIL_SERVER_USER ?? process.env.SMTP_USER;
  const pass = process.env.EMAIL_SERVER_PASSWORD ?? process.env.SMTP_PASS;

  return {
    host,
    port,
    auth: user && pass ? { user, pass } : undefined,
    secure: port === 465,
  };
}

export const authOptions: NextAuthConfig = {
  adapter,
  session: { strategy: "database" },
  pages: {
    signIn: "/signin",
    verifyRequest: "/signin/verify",
  },
  providers: [
    EmailProvider({
      from: emailFrom,
      maxAge: 10 * 60,
      async sendVerificationRequest({ identifier, url }) {
        const server = buildEmailServer();
        const transport = nodemailer.createTransport(server);
        const to = normalizeEmail(identifier);
        await transport.sendMail({
          to,
          from: emailFrom,
          subject: "Your Atticus magic link",
          text: `Sign in to Atticus by opening this link:\n${url}\n`,
          html: `<p>Sign in to Atticus by selecting the button below.</p><p><a href="${url}">Complete sign-in</a></p>`,
        });
        await persistMagicLink(to, url);
      },
    }),
  ],
  secret: process.env.AUTH_SECRET,
  callbacks: {
    async jwt({ token, user }: JwtCallbackParams) {
      if (user) {
        token.userId = user.id;
        token.role = (user as AdapterUser & { role?: Role }).role ?? Role.USER;
        token.orgId = (user as AdapterUser & { orgId?: string }).orgId ?? defaultOrgId;
      }
      return token;
    },
    async session({ session, token }: SessionCallbackParams) {
      if (session.user && "userId" in token && token.userId) {
        const enrichedUser = session.user as NonNullable<Session["user"]>;
        enrichedUser.id = token.userId as string;
        enrichedUser.role = (token.role as Role | undefined) ?? Role.USER;
        enrichedUser.orgId = (token.orgId as string | undefined) ?? defaultOrgId;
      }
      return session;
    },
    async signIn({ user }: SignInCallbackParams) {
      if (!user.email) {
        return false;
      }
      const normalized = normalizeEmail(user.email);
      const existing = await prisma.user.findUnique({ where: { email: normalized } });
      if (!existing) {
        return false;
      }
      if (!existing.orgId) {
        await prisma.user.update({
          where: { id: existing.id },
          data: { orgId: defaultOrgId },
        });
      }
      return true;
    },
  },
  events: {
    async createUser({ user }: CreateUserEventParams) {
      if (!user.email) {
        return;
      }
      await prisma.user.update({
        where: { id: user.id },
        data: {
          email: normalizeEmail(user.email),
          orgId: (user as AdapterUser & { orgId?: string }).orgId ?? defaultOrgId,
          role: (user as AdapterUser & { role?: Role }).role ?? Role.USER,
        },
      });
    },
  },
};

export function getServerAuthSession(): Promise<Session | null> {
  return getServerSession(authOptions);
}

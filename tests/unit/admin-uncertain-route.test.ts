import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Role } from "@prisma/client";
import type { Session } from "next-auth";

const mockGetServerAuthSession = vi.hoisted(() => vi.fn<[], Promise<Session | null>>());
const mockWithRlsContext = vi.hoisted(() => vi.fn());

vi.mock("@/lib/auth", () => ({
  getServerAuthSession: mockGetServerAuthSession,
}));

vi.mock("@/lib/rls", () => ({
  withRlsContext: mockWithRlsContext,
}));

function buildSession(role: Role): Session {
  return {
    user: {
      id: `user-${role.toLowerCase()}`,
      email: `${role.toLowerCase()}@atticus.dev`,
      name: `${role} Test`,
      role,
      orgId: "org-atticus",
    },
    expires: new Date(Date.now() + 60_000).toISOString(),
  };
}

beforeEach(() => {
  vi.resetModules();
  mockGetServerAuthSession.mockReset();
  mockWithRlsContext.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("/api/admin/uncertain GET", () => {
  it("returns 401 when no session is present", async () => {
    mockGetServerAuthSession.mockResolvedValue(null);

    const { GET } = await import("@/app/api/admin/uncertain/route");
    const response = await GET();

    expect(response.status).toBe(401);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "unauthorized" });
  });

  it("rejects standard users", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.USER));

    const { GET } = await import("@/app/api/admin/uncertain/route");
    const response = await GET();

    expect(response.status).toBe(403);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "forbidden" });
  });

  it("lists pending chats for reviewers", async () => {
    const session = buildSession(Role.REVIEWER);
    mockGetServerAuthSession.mockResolvedValue(session);
    const findMany = vi.fn().mockResolvedValue([
      {
        id: "chat-1",
        question: "Why are alerts firing?",
        confidence: 0.42,
        status: "pending_review",
        requestId: "req-123",
        createdAt: new Date("2024-07-10T10:00:00Z"),
        topSources: [
          { path: "content/doc-1.pdf#3", score: 0.81 },
          { path: "content/runbook.md#alerts" },
        ],
        author: { id: "user-author", email: "author@atticus.dev", name: "Author" },
        reviewer: null,
        tickets: [],
      },
    ]);
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        chat: { findMany },
      } as never)
    );

    const { GET } = await import("@/app/api/admin/uncertain/route");
    const response = await GET();

    expect(response.status).toBe(200);
    const payload = (await response.json()) as Array<Record<string, unknown>>;
    expect(findMany).toHaveBeenCalledTimes(1);
    expect(payload).toEqual([
      expect.objectContaining({
        id: "chat-1",
        confidence: 0.42,
        requestId: "req-123",
        topSources: [
          expect.objectContaining({ path: "content/doc-1.pdf#3" }),
          expect.objectContaining({ path: "content/runbook.md#alerts" }),
        ],
      }),
    ]);
  });
});

describe("/api/admin/uncertain/:id/approve POST", () => {
  it("prevents standard users from approving chats", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.USER));

    const { POST } = await import("@/app/api/admin/uncertain/[id]/approve/route");
    const response = await POST(new Request("http://localhost"), { params: { id: "chat-1" } });

    expect(response.status).toBe(403);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "forbidden" });
  });

  it("approves pending chats for reviewers", async () => {
    const session = buildSession(Role.REVIEWER);
    mockGetServerAuthSession.mockResolvedValue(session);
    const findUnique = vi.fn().mockResolvedValue({ status: "pending_review", auditLog: [] });
    const update = vi.fn().mockResolvedValue({
      id: "chat-1",
      status: "reviewed",
      reviewedAt: new Date("2024-07-10T12:00:00Z"),
      reviewer: { id: session.user.id, email: session.user.email, name: session.user.name },
      auditLog: [
        {
          action: "approve",
          actorId: session.user.id,
        },
      ],
    });
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        chat: {
          findUnique,
          update,
        },
      } as never)
    );

    const { POST } = await import("@/app/api/admin/uncertain/[id]/approve/route");
    const response = await POST(new Request("http://localhost"), { params: { id: "chat-1" } });

    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(findUnique).toHaveBeenCalledWith({ where: { id: "chat-1" }, select: { auditLog: true, status: true } });
    expect(update).toHaveBeenCalledTimes(1);
    expect(payload).toMatchObject({ status: "reviewed" });
  });
});

describe("/api/admin/uncertain/:id/escalate POST", () => {
  it("requires admin role", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.REVIEWER));

    const { POST } = await import("@/app/api/admin/uncertain/[id]/escalate/route");
    const response = await POST(new Request("http://localhost"), { params: { id: "chat-1" } });

    expect(response.status).toBe(403);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "forbidden" });
  });

  it("creates a ticket when escalation succeeds", async () => {
    const session = buildSession(Role.ADMIN);
    mockGetServerAuthSession.mockResolvedValue(session);
    const findUnique = vi.fn().mockResolvedValue({
      id: "chat-2",
      orgId: session.user.orgId,
      status: "pending_review",
      question: "Example question",
      auditLog: [],
    });
    const ticketCreate = vi.fn().mockResolvedValue({
      id: "ticket-1",
      key: "AE-202410-01",
      status: "open",
      assignee: "Ops",
      lastActivity: new Date("2024-10-01T12:00:00Z"),
    });
    const chatUpdate = vi.fn().mockResolvedValue({});
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        chat: {
          findUnique,
          update: chatUpdate,
        },
        ticket: {
          create: ticketCreate,
        },
      } as never)
    );

    const { POST } = await import("@/app/api/admin/uncertain/[id]/escalate/route");
    const response = await POST(new Request("http://localhost", { method: "POST" }), {
      params: { id: "chat-2" },
    });

    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(findUnique).toHaveBeenCalledTimes(1);
    expect(ticketCreate).toHaveBeenCalledTimes(1);
    expect(chatUpdate).toHaveBeenCalledTimes(1);
    expect(payload).toMatchObject({ key: "AE-202410-01" });
  });
});

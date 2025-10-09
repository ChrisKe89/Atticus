import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GlossaryStatus, Role } from "@prisma/client";
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

describe("/api/glossary route RBAC", () => {
  it("allows reviewers to list glossary entries", async () => {
    const session = buildSession(Role.REVIEWER);
    mockGetServerAuthSession.mockResolvedValue(session);
    const now = new Date("2024-06-01T12:00:00Z");
    const findMany = vi.fn().mockResolvedValue([
      {
        id: "entry-1",
        term: "Managed Print Services",
        definition: "Full printer fleet management.",
        synonyms: ["MPS"],
        status: GlossaryStatus.APPROVED,
        createdAt: now,
        updatedAt: now,
        reviewedAt: now,
        reviewNotes: "Cleared for launch",
        author: { id: "user-author", email: "author@atticus.dev", name: "Author" },
        updatedBy: { id: "user-admin", email: "admin@atticus.dev", name: "Admin" },
        reviewer: { id: "user-admin", email: "admin@atticus.dev", name: "Admin" },
      },
    ]);
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        glossaryEntry: {
          findMany,
        },
      } as never)
    );

    const { GET } = await import("@/app/api/glossary/route");
    const response = await GET();
    expect(response.status).toBe(200);
    const payload = (await response.json()) as Array<Record<string, unknown>>;
    expect(findMany).toHaveBeenCalledTimes(1);
    expect(payload).toEqual([
      expect.objectContaining({
        term: "Managed Print Services",
        status: GlossaryStatus.APPROVED,
        reviewedAt: now.toISOString(),
        author: expect.objectContaining({ email: "author@atticus.dev" }),
      }),
    ]);
  });

  it("returns 401 when no session is available", async () => {
    mockGetServerAuthSession.mockResolvedValue(null);

    const { GET } = await import("@/app/api/glossary/route");
    const response = await GET();
    expect(response.status).toBe(401);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "unauthorized" });
    expect(mockWithRlsContext).not.toHaveBeenCalled();
  });

  it("prevents reviewers from creating glossary entries", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.REVIEWER));

    const { POST } = await import("@/app/api/glossary/route");
    const request = new Request("http://localhost/api/glossary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ term: "New", definition: "Example" }),
    });

    const response = await POST(request);
    expect(response.status).toBe(403);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "forbidden" });
    expect(mockWithRlsContext).not.toHaveBeenCalled();
  });

  it("allows admins to create glossary entries", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.ADMIN));
    const createdAt = new Date("2024-07-01T08:30:00Z");
    const create = vi.fn().mockResolvedValue({
      id: "entry-2",
      term: "Proactive Maintenance",
      definition: "Predictive device upkeep",
      synonyms: ["Preventative maintenance"],
      status: GlossaryStatus.PENDING,
      createdAt,
      updatedAt: createdAt,
      reviewedAt: null,
      reviewNotes: null,
      author: { id: "user-admin", email: "admin@atticus.dev", name: "Admin" },
      updatedBy: { id: "user-admin", email: "admin@atticus.dev", name: "Admin" },
      reviewer: null,
    });
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        glossaryEntry: {
          create,
        },
      } as never)
    );

    const { POST } = await import("@/app/api/glossary/route");
    const request = new Request("http://localhost/api/glossary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        term: "Proactive Maintenance",
        definition: "Predictive device upkeep",
        synonyms: ["Preventative maintenance"],
        status: "pending",
      }),
    });

    const response = await POST(request);
    expect(response.status).toBe(201);
    const payload = await response.json();
    expect(payload).toMatchObject({ term: "Proactive Maintenance", status: GlossaryStatus.PENDING });
    expect(create).toHaveBeenCalledTimes(1);
  });
});

describe("/api/glossary/[id] route RBAC", () => {
  it("prevents reviewers from updating glossary entries", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(Role.REVIEWER));

    const { PATCH } = await import("@/app/api/glossary/[id]/route");
    const request = new Request("http://localhost/api/glossary/entry-1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "approved" }),
    });

    const response = await PATCH(request, { params: { id: "entry-1" } });
    expect(response.status).toBe(403);
    const payload = await response.json();
    expect(payload).toMatchObject({ error: "forbidden" });
    expect(mockWithRlsContext).not.toHaveBeenCalled();
  });

  it("allows admins to approve entries and stamps reviewer metadata", async () => {
    const session = buildSession(Role.ADMIN);
    mockGetServerAuthSession.mockResolvedValue(session);
    const updatedAt = new Date("2024-07-02T09:00:00Z");
    const update = vi.fn().mockResolvedValue({
      id: "entry-1",
      term: "Managed Print Services",
      definition: "Full printer fleet management.",
      synonyms: ["MPS"],
      status: GlossaryStatus.APPROVED,
      createdAt: updatedAt,
      updatedAt,
      reviewedAt: updatedAt,
      reviewNotes: "Cleared",
      author: { id: "user-author", email: "author@atticus.dev", name: "Author" },
      updatedBy: { id: session.user.id, email: session.user.email, name: session.user.name },
      reviewer: { id: session.user.id, email: session.user.email, name: session.user.name },
    });
    mockWithRlsContext.mockImplementation(async (_session, callback) =>
      callback({
        glossaryEntry: {
          update,
        },
      } as never)
    );

    const { PATCH } = await import("@/app/api/glossary/[id]/route");
    const request = new Request("http://localhost/api/glossary/entry-1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "approved", reviewNotes: "Cleared" }),
    });

    const response = await PATCH(request, { params: { id: "entry-1" } });
    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(payload).toMatchObject({
      status: GlossaryStatus.APPROVED,
      reviewer: expect.objectContaining({ email: session.user.email }),
      reviewNotes: "Cleared",
    });
    expect(update).toHaveBeenCalledTimes(1);
  });
});

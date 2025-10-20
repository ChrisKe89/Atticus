import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "@/app/api/admin/metrics/route";

function createRequest(): NextRequest {
  return new NextRequest("http://localhost:3000/api/admin/metrics");
}

describe("app/api/admin/metrics proxy", () => {
  const originalToken = process.env.ADMIN_API_TOKEN;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    process.env.ADMIN_API_TOKEN = originalToken;
  });

  it("forwards ADMIN_API_TOKEN when configured", async () => {
    process.env.ADMIN_API_TOKEN = "test-admin-token";
    const payload = { queries: 5 };
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } }));

    const response = await GET(createRequest());
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [target, init] = fetchSpy.mock.calls[0];
    expect(target).toBe("http://localhost:8000/admin/metrics");
    const headers = new Headers(init?.headers as HeadersInit);
    expect(headers.get("X-Admin-Token")).toBe("test-admin-token");
    expect(headers.get("Accept")).toBe("application/json");

    const body = await response.json();
    expect(body).toEqual(payload);
  });

  it("omits X-Admin-Token when no token is configured", async () => {
    delete process.env.ADMIN_API_TOKEN;
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify({ queries: 0 }), { status: 200, headers: { "Content-Type": "application/json" } }));

    await GET(createRequest());
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [, init] = fetchSpy.mock.calls[0];
    const headers = new Headers(init?.headers as HeadersInit);
    expect(headers.has("X-Admin-Token")).toBe(false);
  });
});


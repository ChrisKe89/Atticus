import { describe, expect, it } from "vitest";

import { sseEventSchema } from "@/lib/sse-events";

describe("sseEventSchema", () => {
  it("validates start/end events with requestId", () => {
    const start = sseEventSchema.parse({ type: "start", requestId: "req-123" });
    expect(start.requestId).toBe("req-123");

    const end = sseEventSchema.parse({ type: "end", requestId: "req-123" });
    expect(end.requestId).toBe("req-123");
  });

  it("rejects end events missing requestId", () => {
    expect(() => sseEventSchema.parse({ type: "end" })).toThrowError();
  });
});

import { NextResponse } from "next/server";
import {
  atticusFetch,
  extractTraceHeaders,
  resolveRequestIds,
} from "@admin/lib/atticus-client";

export async function POST(request: Request) {
  const ids = resolveRequestIds({ headers: request.headers });
  const body = await request.json().catch(() => ({}));
  const upstream = await atticusFetch("/api/glossary", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify(body),
  });
  const payload = await upstream.json().catch(() => ({}));
  return NextResponse.json(payload, {
    status: upstream.status,
    headers: extractTraceHeaders(upstream, ids),
  });
}

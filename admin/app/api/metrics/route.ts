import { NextResponse } from "next/server";
import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "@admin/lib/atticus-client";

export async function GET(request: Request) {
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/admin/metrics", {
    headers: {
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}





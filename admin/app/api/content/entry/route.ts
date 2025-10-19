import { NextResponse } from "next/server";
import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "@admin/lib/atticus-client";

export async function DELETE(request: Request) {
  const payload = await request.json().catch(() => ({}));
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/admin/content/entry", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify(payload),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}





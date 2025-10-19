import { NextResponse } from "next/server";
import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "@admin/lib/atticus-client";

export async function POST(request: Request) {
  const formData = await request.formData();
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/admin/content/upload", {
    method: "POST",
    headers: {
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: formData,
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}





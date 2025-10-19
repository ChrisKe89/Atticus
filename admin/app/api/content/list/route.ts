import { NextResponse } from "next/server";
import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "@admin/lib/atticus-client";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const pathParam = url.searchParams.get("path") ?? ".";
  const target = `/api/admin/content/list?path=${encodeURIComponent(pathParam)}`;
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch(target, {
    headers: {
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}





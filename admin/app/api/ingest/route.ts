import { NextResponse } from "next/server";

import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "../../../lib/atticus-client";

type IngestPayload = {
  fullRefresh?: boolean;
  paths?: string[];
};

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as Partial<IngestPayload>;
  const paths = Array.isArray(payload.paths)
    ? payload.paths.map((item) => item.trim()).filter(Boolean)
    : [];
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/ingest", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify({
      full_refresh: Boolean(payload.fullRefresh),
      paths: paths.length > 0 ? paths : undefined,
    }),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}

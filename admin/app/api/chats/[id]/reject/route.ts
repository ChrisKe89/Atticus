import { NextResponse } from "next/server";
import {
  atticusFetch,
  extractTraceHeaders,
  resolveRequestIds,
} from "../../../../../lib/atticus-client";

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch(`/api/admin/uncertain/${params.id}/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify({ notes: "Rejected via admin service" }),
  });

  let payload: unknown = null;
  try {
    payload = await upstream.json();
  } catch {
    payload = null;
  }

  if (!upstream.ok) {
    return NextResponse.json(
      payload ?? { error: "upstream_error", detail: "Unable to reject chat." },
      { status: upstream.status, headers: extractTraceHeaders(upstream, ids) }
    );
  }

  return NextResponse.json(payload ?? { ok: true }, { headers: extractTraceHeaders(upstream, ids) });
}

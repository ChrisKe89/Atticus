import { NextResponse } from "next/server";
import {
  atticusFetch,
  extractTraceHeaders,
  resolveRequestIds,
} from "../../../../../lib/atticus-client";

type DraftPayload = {
  answer?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveRequestIds({ headers: request.headers });
  const body = (await request.json().catch(() => ({}))) as DraftPayload;
  const answer = body.answer?.trim() ?? "";
  if (!answer) {
    return NextResponse.json(
      { error: "invalid_request", detail: "Draft answer must not be empty." },
      { status: 400, headers: { "X-Request-ID": ids.requestId, "X-Trace-ID": ids.traceId } }
    );
  }

  const upstream = await atticusFetch(`/api/admin/uncertain/${params.id}/save-draft`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify({ answer }),
  });

  let payload: unknown = null;
  try {
    payload = await upstream.json();
  } catch {
    payload = null;
  }

  if (!upstream.ok) {
    return NextResponse.json(
      payload ?? { error: "upstream_error", detail: "Unable to save draft." },
      { status: upstream.status, headers: extractTraceHeaders(upstream, ids) }
    );
  }

  return NextResponse.json(payload ?? { ok: true }, { headers: extractTraceHeaders(upstream, ids) });
}

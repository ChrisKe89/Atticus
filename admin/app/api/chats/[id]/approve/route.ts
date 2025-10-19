import { NextResponse } from "next/server";
import {
  atticusFetch,
  extractTraceHeaders,
  resolveRequestIds,
} from "../../../../../lib/atticus-client";
import { deriveCsvTarget, appendChatCsvRecord } from "../../../../../lib/csv";
import { getReviewerIdentity } from "../../../../../lib/config";
import { logPhaseTwoError } from "../../../../../lib/logging";
import type { SourceSummary } from "../../../../../lib/types";

type ApprovePayload = {
  question?: string;
  answer?: string;
  topSources?: SourceSummary[];
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const ids = resolveRequestIds({ headers: request.headers });
  const body = (await request.json().catch(() => ({}))) as ApprovePayload;
  const answer = body.answer?.trim() ?? "";
  if (!answer) {
    return NextResponse.json(
      { error: "invalid_request", detail: "Answer must not be empty." },
      { status: 400, headers: { "X-Request-ID": ids.requestId, "X-Trace-ID": ids.traceId } }
    );
  }

  const upstream = await atticusFetch(`/api/admin/uncertain/${params.id}/approve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify({ answer }),
  });

  let upstreamPayload: unknown = null;
  try {
    upstreamPayload = await upstream.json();
  } catch {
    upstreamPayload = null;
  }

  if (!upstream.ok) {
    return NextResponse.json(
      upstreamPayload ?? { error: "upstream_error", detail: "Approval failed upstream." },
      { status: upstream.status, headers: extractTraceHeaders(upstream, ids) }
    );
  }

  const sources = Array.isArray(body.topSources) ? body.topSources : [];
  const { family, model } = deriveCsvTarget(sources);
  const reviewer = getReviewerIdentity();

  try {
    await appendChatCsvRecord({
      family,
      model,
      question: body.question ?? "Unknown question",
      answer,
      reviewer: reviewer.name,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown CSV error";
    await logPhaseTwoError(`Failed to append CSV for chat ${params.id}: ${message}`);
  }

  return NextResponse.json(upstreamPayload ?? { ok: true }, { headers: extractTraceHeaders(upstream, ids) });
}

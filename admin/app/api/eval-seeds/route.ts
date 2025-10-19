import { NextResponse } from "next/server";

import { atticusFetch, extractTraceHeaders, resolveRequestIds } from "../../../lib/atticus-client";

type EvalSeedInput = {
  question: string;
  relevantDocuments?: string[];
  expectedAnswer?: string | null;
  notes?: string | null;
};

type EvalSeedPayload = {
  seeds: EvalSeedInput[];
};

export async function GET(request: Request) {
  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/admin/eval-seeds", {
    headers: {
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => ({}))) as Partial<EvalSeedPayload>;
  const seeds = Array.isArray(payload.seeds) ? payload.seeds : [];
  const normalized: EvalSeedInput[] = seeds.map((seed) => ({
    question: seed.question?.trim() ?? "",
    relevantDocuments: Array.isArray(seed.relevantDocuments)
      ? seed.relevantDocuments.map((doc) => doc.trim()).filter(Boolean)
      : [],
    expectedAnswer: seed.expectedAnswer?.trim() ?? null,
    notes: seed.notes?.trim() ?? null,
  }));

  const ids = resolveRequestIds({ headers: request.headers });
  const upstream = await atticusFetch("/api/admin/eval-seeds", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": ids.requestId,
      "X-Trace-ID": ids.traceId,
    },
    body: JSON.stringify({ seeds: normalized }),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status, headers: extractTraceHeaders(upstream, ids) });
}

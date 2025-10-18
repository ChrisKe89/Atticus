import { NextResponse } from "next/server";

import { atticusFetch } from "../../../lib/atticus-client";

type EvalSeedInput = {
  question: string;
  relevantDocuments?: string[];
  expectedAnswer?: string | null;
  notes?: string | null;
};

type EvalSeedPayload = {
  seeds: EvalSeedInput[];
};

export async function GET() {
  const upstream = await atticusFetch("/api/admin/eval-seeds");
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
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

  const upstream = await atticusFetch("/api/admin/eval-seeds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ seeds: normalized }),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}

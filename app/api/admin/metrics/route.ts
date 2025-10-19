import { NextResponse } from "next/server";

function getMetricsServiceUrl(): string {
  const base =
    process.env.RAG_SERVICE_URL ??
    process.env.RETRIEVAL_SERVICE_URL ??
    process.env.ASK_SERVICE_URL ??
    "http://localhost:8000";
  return base.replace(/\/+$/, "");
}

export async function GET() {
  const target = `${getMetricsServiceUrl()}/admin/metrics`;
  try {
    const upstream = await fetch(target, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const body = await upstream.json().catch(() => ({}));
    return NextResponse.json(body, { status: upstream.status });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to contact metrics service.";
    return NextResponse.json({ error: "upstream_error", detail }, { status: 502 });
  }
}


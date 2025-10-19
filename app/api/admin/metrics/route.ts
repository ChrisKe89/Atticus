import type { NextRequest } from "next/server";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

function getMetricsServiceUrl(): string {
  const base =
    process.env.RAG_SERVICE_URL ??
    process.env.RETRIEVAL_SERVICE_URL ??
    process.env.ASK_SERVICE_URL ??
    "http://localhost:8000";
  return base.replace(/\/+$/, "");
}

export async function GET(request: NextRequest) {
  const ids = resolveTraceIdentifiers(request);
  const target = `${getMetricsServiceUrl()}/admin/metrics`;
  try {
    const upstream = await fetch(target, {
      headers: {
        Accept: "application/json",
        "X-Request-ID": ids.requestId,
        "X-Trace-ID": ids.traceId,
      },
      cache: "no-store",
    });
    const body = await upstream.json().catch(() => ({}));
    return jsonWithTrace(body, ids, { status: upstream.status });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to contact metrics service.";
    return jsonWithTrace({ error: "upstream_error", detail }, ids, { status: 502 });
  }
}


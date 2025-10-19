import type { NextRequest } from "next/server";
import { listContent } from "@/lib/content-manager";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

export async function GET(request: NextRequest) {
  const ids = resolveTraceIdentifiers(request);
  const relativePath = request.nextUrl.searchParams.get("path") ?? ".";
  try {
    const entries = await listContent(relativePath);
    return jsonWithTrace({ entries }, ids);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to list content.";
    return jsonWithTrace({ error: message }, ids, { status: 400 });
  }
}


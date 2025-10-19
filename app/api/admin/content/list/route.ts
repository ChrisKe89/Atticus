import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { listContent } from "@/lib/content-manager";

export async function GET(request: NextRequest) {
  const relativePath = request.nextUrl.searchParams.get("path") ?? ".";
  try {
    const entries = await listContent(relativePath);
    return NextResponse.json({ entries });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to list content.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}


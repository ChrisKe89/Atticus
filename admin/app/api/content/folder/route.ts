import { NextResponse } from "next/server";
import { atticusFetch } from "@admin/lib/atticus-client";

export async function POST(request: Request) {
  const payload = await request.json().catch(() => ({}));
  const upstream = await atticusFetch("/api/admin/content/folder", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}





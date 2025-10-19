import { NextResponse } from "next/server";
import { atticusFetch } from "@admin/lib/atticus-client";

export async function DELETE(request: Request) {
  const payload = await request.json().catch(() => ({}));
  const upstream = await atticusFetch("/api/admin/content/entry", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}





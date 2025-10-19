import { NextResponse } from "next/server";
import { atticusFetch } from "@admin/lib/atticus-client";

export async function POST() {
  const upstream = await atticusFetch("/api/admin/content/reingest", { method: "POST" });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}





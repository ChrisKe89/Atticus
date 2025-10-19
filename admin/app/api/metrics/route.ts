import { NextResponse } from "next/server";
import { atticusFetch } from "@admin/lib/atticus-client";

export async function GET() {
  const upstream = await atticusFetch("/api/admin/metrics");
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}





import { NextResponse } from "next/server";
import { atticusFetch } from "@admin/lib/atticus-client";

export async function POST(request: Request) {
  const formData = await request.formData();
  const upstream = await atticusFetch("/api/admin/content/upload", {
    method: "POST",
    body: formData,
  });
  const body = await upstream.json().catch(() => ({}));
  return NextResponse.json(body, { status: upstream.status });
}





import { NextResponse } from "next/server";
import { atticusFetch } from "../../../../../lib/atticus-client";

export async function POST(_: Request, { params }: { params: { id: string } }) {
  const upstream = await atticusFetch(`/api/admin/uncertain/${params.id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes: "Rejected via admin service" }),
  });

  let payload: unknown = null;
  try {
    payload = await upstream.json();
  } catch {
    payload = null;
  }

  if (!upstream.ok) {
    return NextResponse.json(
      payload ?? { error: "upstream_error", detail: "Unable to reject chat." },
      { status: upstream.status }
    );
  }

  return NextResponse.json(payload ?? { ok: true });
}

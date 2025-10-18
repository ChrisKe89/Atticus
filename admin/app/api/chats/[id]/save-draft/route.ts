import { NextResponse } from "next/server";
import { atticusFetch } from "../../../../../lib/atticus-client";

type DraftPayload = {
  answer?: string;
};

export async function POST(request: Request, { params }: { params: { id: string } }) {
  const body = (await request.json().catch(() => ({}))) as DraftPayload;
  const answer = body.answer?.trim() ?? "";
  if (!answer) {
    return NextResponse.json({ error: "invalid_request", detail: "Draft answer must not be empty." }, { status: 400 });
  }

  const upstream = await atticusFetch(`/api/admin/uncertain/${params.id}/save-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answer }),
  });

  let payload: unknown = null;
  try {
    payload = await upstream.json();
  } catch {
    payload = null;
  }

  if (!upstream.ok) {
    return NextResponse.json(
      payload ?? { error: "upstream_error", detail: "Unable to save draft." },
      { status: upstream.status }
    );
  }

  return NextResponse.json(payload ?? { ok: true });
}

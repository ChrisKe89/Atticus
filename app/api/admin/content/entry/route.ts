import { NextResponse } from "next/server";
import { deleteEntry } from "@/lib/content-manager";

type Payload = {
  path?: string;
};

export async function DELETE(request: Request) {
  const body = (await request.json().catch(() => ({}))) as Payload;
  if (!body.path) {
    return NextResponse.json({ error: "Path is required." }, { status: 400 });
  }
  try {
    await deleteEntry(body.path);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to delete entry.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}


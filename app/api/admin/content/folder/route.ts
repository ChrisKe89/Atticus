import { NextResponse } from "next/server";
import { ensureFolder } from "@/lib/content-manager";

type Payload = {
  parentPath?: string;
  folderName?: string;
};

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as Payload;
  if (!body.folderName) {
    return NextResponse.json({ error: "Folder name is required." }, { status: 400 });
  }
  try {
    const storedPath = await ensureFolder(body.parentPath, body.folderName);
    return NextResponse.json({ path: storedPath });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to create folder.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

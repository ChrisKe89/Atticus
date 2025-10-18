import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { saveFile } from "@/lib/content-manager";

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const targetPath = typeof formData.get("path") === "string" ? (formData.get("path") as string) : ".";
  const file = formData.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ error: "Missing file upload." }, { status: 400 });
  }

  const buffer = Buffer.from(await file.arrayBuffer());
  try {
    const storedPath = await saveFile(targetPath, file.name, buffer);
    return NextResponse.json({ path: storedPath, size: buffer.length });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to save file.";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}

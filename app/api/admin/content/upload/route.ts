import type { NextRequest } from "next/server";
import { saveFile } from "@/lib/content-manager";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

export async function POST(request: NextRequest) {
  const ids = resolveTraceIdentifiers(request);
  const formData = await request.formData();
  const targetPath = typeof formData.get("path") === "string" ? (formData.get("path") as string) : ".";
  const file = formData.get("file");
  if (!(file instanceof File)) {
    return jsonWithTrace({ error: "Missing file upload." }, ids, { status: 400 });
  }

  const buffer = Buffer.from(await file.arrayBuffer());
  try {
    const storedPath = await saveFile(targetPath, file.name, buffer);
    return jsonWithTrace({ path: storedPath, size: buffer.length }, ids);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to save file.";
    return jsonWithTrace({ error: message }, ids, { status: 400 });
  }
}


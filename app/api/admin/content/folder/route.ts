import { ensureFolder } from "@/lib/content-manager";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

type Payload = {
  parentPath?: string;
  folderName?: string;
};

export async function POST(request: Request) {
  const ids = resolveTraceIdentifiers(request);
  const body = (await request.json().catch(() => ({}))) as Payload;
  if (!body.folderName) {
    return jsonWithTrace({ error: "Folder name is required." }, ids, { status: 400 });
  }
  try {
    const storedPath = await ensureFolder(body.parentPath, body.folderName);
    return jsonWithTrace({ path: storedPath }, ids);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to create folder.";
    return jsonWithTrace({ error: message }, ids, { status: 400 });
  }
}


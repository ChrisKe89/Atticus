import { deleteEntry } from "@/lib/content-manager";
import { jsonWithTrace, resolveTraceIdentifiers } from "@/lib/trace-headers";

type Payload = {
  path?: string;
};

export async function DELETE(request: Request) {
  const ids = resolveTraceIdentifiers(request);
  const body = (await request.json().catch(() => ({}))) as Payload;
  if (!body.path) {
    return jsonWithTrace({ error: "Path is required." }, ids, { status: 400 });
  }
  try {
    await deleteEntry(body.path);
    return jsonWithTrace({ ok: true }, ids);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unable to delete entry.";
    return jsonWithTrace({ error: message }, ids, { status: 400 });
  }
}


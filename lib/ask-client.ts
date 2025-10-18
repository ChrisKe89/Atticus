import {
  askRequestSchema,
  askResponseSchema,
  type AskRequest,
  type AskResponse,
} from "@/lib/ask-contract";
import {
  type AskStreamEvent,
  sseEventSchema,
  type SseAnswerEvent,
  type SseEndEvent,
  type SseStartEvent,
} from "@/lib/sse-events";

interface StreamOptions {
  signal?: AbortSignal;
  onEvent?: (event: AskStreamEvent) => void;
}

function parseSseChunk(chunk: string): AskStreamEvent | null {
  const lines = chunk.split("\n").filter(Boolean);
  let eventType = "answer";
  let dataLine = "";
  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    }
    if (line.startsWith("data:")) {
      dataLine += line.slice(5).trim();
    }
  }
  if (!dataLine) {
    return null;
  }
  const payload = JSON.parse(dataLine);
  if (eventType === "start" || eventType === "end") {
    const normalised: SseStartEvent | SseEndEvent = sseEventSchema.parse({
      type: eventType,
      requestId: payload.request_id ?? payload.requestId ?? "",
    }) as SseStartEvent | SseEndEvent;
    return normalised;
  }
  const answer: SseAnswerEvent = sseEventSchema.parse({ type: "answer", payload }) as SseAnswerEvent;
  return answer;
}

export async function streamAsk(
  request: AskRequest,
  options: StreamOptions = {}
): Promise<AskResponse> {
  const normalized = askRequestSchema.parse(request);
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(normalized),
    signal: options.signal,
  });

  if (!response.ok) {
    // Try to parse JSON error payload and map to a friendly message
    let friendly = "Something went wrong. Please try again.";
    const ct = response.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
      try {
        const errJson = await response.json();
        const code = (errJson?.error as string | undefined) ?? "";
        const detail = (errJson?.detail as string | undefined) ?? "";
        if (response.status === 400 || code === "bad_request") {
          friendly =
            "There is no context to that question or it is not a proper question, please try again";
        } else if (typeof detail === "string" && detail) {
          friendly = detail;
        }
      } catch {
        // fall back to text below
      }
    }
    if (!ct.includes("application/json")) {
      try {
        const text = await response.text();
        if (text) friendly = text;
      } catch {
        // ignore
      }
    }
    throw new Error(friendly);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("text/event-stream")) {
    const payload = await response.json();
    return askResponseSchema.parse(payload);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Streaming unsupported in this environment.");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let resolved: AskResponse | undefined;

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const chunk = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = parseSseChunk(chunk);
      if (event) {
        options.onEvent?.(event);
        if (event.type === "answer") {
          resolved = event.payload;
        }
      }
      boundary = buffer.indexOf("\n\n");
    }
  }

  if (!resolved) {
    throw new Error("Stream ended without answer payload.");
  }
  return resolved;
}

export type { AskStreamEvent } from "@/lib/sse-events";

import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";
import { askRequestSchema, askResponseSchema } from "@/lib/ask-contract";
import type { AskRequest } from "@/lib/ask-contract";
import { captureLowConfidenceChat } from "@/lib/chat-capture";

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function getServiceUrl() {
  const raw = process.env.RAG_SERVICE_URL ?? process.env.ASK_SERVICE_URL ?? "http://localhost:8000";
  return raw.replace(/\/$/, "");
}

function normalizeFields(value: unknown): Record<string, string> | undefined {
  if (!value || typeof value !== "object") {
    return undefined;
  }
  const result: Record<string, string> = {};
  for (const [key, raw] of Object.entries(value)) {
    result[String(key)] = typeof raw === "string" ? raw : JSON.stringify(raw);
  }
  return Object.keys(result).length ? result : undefined;
}

function buildErrorResponse(
  status: number,
  requestId: string,
  error: string,
  detail: string,
  fields?: Record<string, string>
) {
  const payload: Record<string, unknown> = {
    error,
    detail,
    request_id: requestId,
  };
  if (fields) {
    payload.fields = fields;
  }
  return NextResponse.json(payload, {
    status,
    headers: {
      "X-Request-ID": requestId,
    },
  });
}

async function readErrorBody(response: Response, fallbackRequestId: string) {
  const contentType = response.headers.get("content-type") ?? "";
  let parsedBody: unknown = null;
  if (contentType.includes("application/json")) {
    try {
      parsedBody = await response.json();
    } catch (error) {
      return {
        status: response.status === 0 ? 502 : response.status,
        error: "upstream_error",
        detail: "Failed to parse upstream JSON response.",
        requestId: fallbackRequestId,
      } as const;
    }
  } else {
    const text = await response.text();
    parsedBody = text;
  }

  const status = response.status === 0 ? 502 : response.status;
  if (parsedBody && typeof parsedBody === "object" && !Array.isArray(parsedBody)) {
    const body = parsedBody as Record<string, unknown>;
    const requestId = typeof body.request_id === "string" ? body.request_id : fallbackRequestId;
    const error = typeof body.error === "string" ? body.error : "upstream_error";
    const detail = typeof body.detail === "string" ? body.detail : "Unknown upstream error.";
    const fields = normalizeFields(body.fields);
    return { status, error, detail, fields, requestId } as const;
  }

  const detail = typeof parsedBody === "string" && parsedBody.length ? parsedBody : "Unknown upstream error.";
  return { status, error: "upstream_error", detail, requestId: fallbackRequestId } as const;
}

export async function POST(request: Request) {
  const acceptsSse = (request.headers.get("accept") ?? "").includes("text/event-stream");
  const requestId = request.headers.get("x-request-id") ?? randomUUID();

  let parsed: AskRequest;
  try {
    const payload = await request.json();
    parsed = askRequestSchema.parse(payload);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Invalid request payload";
    return buildErrorResponse(400, requestId, "validation_error", detail);
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${getServiceUrl()}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: acceptsSse ? "text/event-stream" : "application/json",
        "X-Request-ID": requestId,
      },
      body: JSON.stringify({
        question: parsed.question,
        filters: parsed.filters ?? undefined,
        contextHints: parsed.contextHints ?? undefined,
        topK: parsed.topK ?? undefined,
        models: parsed.models ?? undefined,
      }),
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Failed to contact retrieval service.";
    return buildErrorResponse(502, requestId, "upstream_unreachable", detail);
  }

  const upstreamRequestId = upstream.headers.get("x-request-id") ?? requestId;

  if (!upstream.ok) {
    const normalized = await readErrorBody(upstream, upstreamRequestId);
    return buildErrorResponse(normalized.status, normalized.requestId, normalized.error, normalized.detail, normalized.fields);
  }

  const contentType = upstream.headers.get("content-type") ?? "";

  if (acceptsSse && contentType.includes("text/event-stream") && upstream.body) {
    const reader = upstream.body.getReader();
    let buffer = "";
    let capturePromise: Promise<void> | null = null;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode(`event: start\ndata: ${JSON.stringify({ request_id: upstreamRequestId })}\n\n`)
        );
      },
      async pull(controller) {
        const { done, value } = await reader.read();
        if (done) {
          if (capturePromise) {
            await capturePromise.catch(() => undefined);
          }
          controller.enqueue(
            encoder.encode(`event: end\ndata: ${JSON.stringify({ request_id: upstreamRequestId })}\n\n`)
          );
          controller.close();
          return;
        }
        if (value) {
          controller.enqueue(value);
          buffer += decoder.decode(value, { stream: true });
          let boundary = buffer.indexOf("\n\n");
          while (boundary !== -1) {
            const rawEvent = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            boundary = buffer.indexOf("\n\n");

            let eventType = "";
            let dataPayload = "";
            for (const rawLine of rawEvent.split("\n")) {
              const line = rawLine.trim();
              if (!line) {
                continue;
              }
              if (line.startsWith("event:")) {
                eventType = line.slice(6).trim();
              } else if (line.startsWith("data:")) {
                const fragment = line.slice(5).trim();
                dataPayload = dataPayload ? `${dataPayload}${fragment}` : fragment;
              }
            }

            if (eventType === "answer" && dataPayload && !capturePromise) {
              try {
                const parsedAnswer = askResponseSchema.parse(JSON.parse(dataPayload));
                capturePromise = captureLowConfidenceChat({
                  question: parsed.question,
                  response: parsedAnswer,
                });
              } catch (error) {
                // Ignore malformed payloads; the client will handle upstream data.
              }
            }
          }
        }
      },
      cancel(reason) {
        reader.cancel(reason).catch(() => undefined);
      },
    });

    return new Response(stream, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "X-Request-ID": upstreamRequestId,
      },
    });
  }

  let askResponse;
  try {
    const raw = await upstream.json();
    askResponse = askResponseSchema.parse(raw);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Invalid upstream response";
    return buildErrorResponse(502, upstreamRequestId, "invalid_upstream_response", detail);
  }

  await captureLowConfidenceChat({ question: parsed.question, response: askResponse });

  if (acceptsSse) {
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode(`event: start\ndata: ${JSON.stringify({ request_id: askResponse.request_id })}\n\n`)
        );
        controller.enqueue(
          encoder.encode(`event: answer\ndata: ${JSON.stringify(askResponse)}\n\n`)
        );
        controller.enqueue(
          encoder.encode(`event: end\ndata: ${JSON.stringify({ request_id: askResponse.request_id })}\n\n`)
        );
        controller.close();
      },
    });

    return new Response(stream, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "X-Request-ID": askResponse.request_id,
      },
    });
  }

  return NextResponse.json(askResponse, {
    status: 200,
    headers: {
      "X-Request-ID": askResponse.request_id,
    },
  });
}

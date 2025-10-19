import { randomUUID } from "node:crypto";
import { NextResponse } from "next/server";

export type TraceIdentifiers = {
  requestId: string;
  traceId: string;
};

type HeaderSource =
  | Headers
  | HeadersInit
  | { headers?: Headers | HeadersInit | null }
  | Request
  | null
  | undefined;

function toHeaders(source?: HeaderSource): Headers {
  if (!source) {
    return new Headers();
  }
  if (source instanceof Headers) {
    return source;
  }
  if (source instanceof Request) {
    return toHeaders(source.headers);
  }
  if (typeof source === "object" && source !== null && "headers" in source) {
    const candidate = (source as { headers?: Headers | HeadersInit | null }).headers;
    if (!candidate) {
      return new Headers();
    }
    return candidate instanceof Headers ? candidate : new Headers(candidate);
  }
  return new Headers(source as HeadersInit);
}

export function resolveTraceIdentifiers(source?: HeaderSource): TraceIdentifiers {
  const fallback = randomUUID();
  const headers = toHeaders(source);
  const requestId = headers.get("x-request-id") ?? fallback;
  const traceId = headers.get("x-trace-id") ?? requestId;
  return { requestId, traceId };
}

type NextResponseInit = Parameters<typeof NextResponse.json>[1];

export function withTraceHeaders(
  init: NextResponseInit | undefined,
  ids: TraceIdentifiers,
): NextResponseInit {
  const headers = new Headers(init?.headers ?? {});
  headers.set("X-Request-ID", ids.requestId);
  headers.set("X-Trace-ID", ids.traceId);
  return {
    ...init,
    headers,
  };
}

export function jsonWithTrace(
  payload: unknown,
  ids: TraceIdentifiers,
  init?: NextResponseInit,
): NextResponse {
  return NextResponse.json(payload, withTraceHeaders(init, ids));
}

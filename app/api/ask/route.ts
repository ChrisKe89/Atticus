import { NextResponse } from 'next/server';
import { askRequestSchema, askResponseSchema } from '@/lib/ask-contract';

const encoder = new TextEncoder();

function getServiceUrl() {
  const raw = process.env.RAG_SERVICE_URL ?? process.env.ASK_SERVICE_URL ?? 'http://localhost:8000';
  return raw.replace(/\/$/, '');
}

async function readErrorBody(response: Response) {
  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (error) {
      return { error: 'upstream_error', detail: 'Failed to parse upstream JSON response.' };
    }
  }
  const text = await response.text();
  return { error: 'upstream_error', detail: text || 'Unknown upstream error.' };
}

export async function POST(request: Request) {
  let parsed;
  try {
    const payload = await request.json();
    parsed = askRequestSchema.parse(payload);
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Invalid request payload';
    return NextResponse.json(
      { error: 'validation_error', detail },
      { status: 400 }
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${getServiceUrl()}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: parsed.question,
        filters: parsed.filters ?? undefined,
        contextHints: parsed.contextHints ?? undefined,
        topK: parsed.topK ?? undefined,
      }),
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Failed to contact retrieval service.';
    return NextResponse.json({ error: 'upstream_unreachable', detail }, { status: 502 });
  }

  if (!upstream.ok) {
    const body = await readErrorBody(upstream);
    const status = upstream.status === 0 ? 502 : upstream.status;
    return NextResponse.json(body, { status });
  }

  let askResponse;
  try {
    const raw = await upstream.json();
    askResponse = askResponseSchema.parse(raw);
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Invalid upstream response';
    return NextResponse.json(
      { error: 'invalid_upstream_response', detail },
      { status: 502 }
    );
  }

  const requestId = askResponse.request_id;
  if ((request.headers.get('accept') ?? '').includes('text/event-stream')) {
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            `event: start\ndata: ${JSON.stringify({ request_id: requestId })}\n\n`
          )
        );
        controller.enqueue(
          encoder.encode(
            `event: answer\ndata: ${JSON.stringify(askResponse)}\n\n`
          )
        );
        controller.enqueue(
          encoder.encode(
            `event: end\ndata: ${JSON.stringify({ request_id: requestId })}\n\n`
          )
        );
        controller.close();
      },
    });

    return new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
        'X-Request-ID': requestId,
      },
    });
  }

  return NextResponse.json(askResponse, {
    status: 200,
    headers: {
      'X-Request-ID': requestId,
    },
  });
}

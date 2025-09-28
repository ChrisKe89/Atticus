import { afterEach, describe, expect, it, vi } from 'vitest';
import { askRequestSchema, askResponseSchema } from '@/lib/ask-contract';
import { streamAsk } from '@/lib/ask-client';

const encoder = new TextEncoder();

function createSseResponse(payload: unknown, requestId = 'req-123') {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(`event: start\ndata: {"request_id":"${requestId}"}\n\n`));
      controller.enqueue(encoder.encode(`event: answer\ndata: ${JSON.stringify(payload)}\n\n`));
      controller.enqueue(encoder.encode(`event: end\ndata: {"request_id":"${requestId}"}\n\n`));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream' },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe('askRequestSchema', () => {
  it('normalises optional fields', () => {
    const parsed = askRequestSchema.parse({
      question: '  hello  ',
      filters: null,
      contextHints: ['  product A  '],
      topK: null,
    });
    expect(parsed.question).toBe('hello');
    expect(parsed.filters).toBeUndefined();
    expect(parsed.contextHints).toEqual(['  product A  ']);
    expect(parsed.topK).toBeUndefined();
  });
});

describe('streamAsk', () => {
  it('parses SSE payloads and resolves with AskResponse', async () => {
    const payload = askResponseSchema.parse({
      answer: 'Yes, the pilot is four weeks.',
      confidence: 0.82,
      should_escalate: false,
      request_id: 'req-123',
      sources: [
        { path: 'content/pilot.pdf', page: 3, heading: 'Implementation timeline', chunkId: 'chunk-1' },
      ],
    });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(createSseResponse(payload));

    const response = await streamAsk({
      question: 'timeline?',
      filters: undefined,
      contextHints: undefined,
      topK: undefined,
    });
    expect(response).toEqual(payload);
  });

  it('falls back to JSON responses when streaming is unavailable', async () => {
    const payload = {
      answer: 'Fallback response',
      confidence: 0.66,
      should_escalate: true,
      request_id: 'req-456',
      sources: [],
    };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    const response = await streamAsk({
      question: 'fallback?',
      filters: undefined,
      contextHints: undefined,
      topK: undefined,
    });
    expect(response).toEqual(askResponseSchema.parse(payload));
  });
});

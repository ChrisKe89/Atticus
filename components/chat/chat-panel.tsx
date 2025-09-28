"use client";

import { useMemo, useState } from "react";
import { Loader2, Paperclip, Send } from "lucide-react";
import { streamAsk, type AskStreamEvent } from "@/lib/ask-client";
import type { AskResponse, AskSource } from "@/lib/ask-contract";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "pending" | "complete" | "error";
  response?: AskResponse;
  error?: string;
}

const shortcuts = [
  { label: "Shift + Enter", description: "New line" },
  { label: "Ctrl + Enter", description: "Send message" },
  { label: "Esc", description: "Clear composer" },
];

const highlights = [
  {
    title: "Grounded responses",
    description:
      "Atticus cites every answer with the supporting evidence so Sales stays audit-ready.",
  },
  {
    title: "Fast ingest pipeline",
    description: "Deterministic chunking keeps the knowledge base fresh without manual clean-up.",
  },
];

function createId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatConfidence(confidence: number | undefined) {
  if (confidence === undefined || Number.isNaN(confidence)) {
    return "—";
  }
  return `${Math.round(confidence * 100)}%`;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: createId(),
      role: "assistant",
      status: "complete",
      content:
        "Hi! Drop any tender or product question below and I will back it with citations from your latest content set.",
    },
  ]);
  const [composer, setComposer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastAssistant = useMemo(
    () => messages.filter((message) => message.role === "assistant").at(-1)?.response,
    [messages]
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = composer.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    setError(null);

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      status: "complete",
      content: trimmed,
    };
    const placeholder: ChatMessage = {
      id: createId(),
      role: "assistant",
      status: "pending",
      content: "Atticus is thinking…",
    };

    setMessages((prev) => [...prev, userMessage, placeholder]);
    setComposer("");
    setIsStreaming(true);

    try {
      await streamAsk(
        { question: trimmed, filters: undefined, contextHints: undefined, topK: undefined },
        {
          onEvent: (event: AskStreamEvent) => {
            if (event.type === "answer") {
              const response = event.payload;
              console.info("ask_response", {
                requestId: response.request_id,
                confidence: response.confidence,
                shouldEscalate: response.should_escalate,
              });
              setMessages((prev) =>
                prev.map((message) =>
                  message.id === placeholder.id
                    ? {
                        ...message,
                        status: "complete",
                        content: response.answer,
                        response,
                      }
                    : message
                )
              );
            }
            if (event.type === "end") {
              setIsStreaming(false);
            }
          },
        }
      );
    } catch (err) {
      setIsStreaming(false);
      const messageError = err instanceof Error ? err.message : "Something went wrong.";
      setError(messageError);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === placeholder.id
            ? {
                ...message,
                status: "error",
                content: "Unable to generate a response. Try again in a few moments.",
                error: messageError,
              }
            : message
        )
      );
    }
  }

  return (
    <section className="grid gap-10 lg:grid-cols-[1.3fr_1fr]">
      <div className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Live conversation
          </h2>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">
            {isStreaming ? "Streaming…" : "Connected"}
          </span>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.map((message) => (
            <article key={message.id} className="flex items-start gap-3">
              <div
                className={
                  message.role === "assistant"
                    ? "flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white"
                    : "flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 text-sm font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                }
              >
                {message.role === "assistant" ? "A" : "You"}
              </div>
              <div
                className={
                  message.role === "assistant"
                    ? "flex-1 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700 shadow-sm dark:bg-slate-800/60 dark:text-slate-200"
                    : "flex-1 rounded-2xl bg-white p-4 text-sm text-slate-700 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-100 dark:ring-slate-800"
                }
              >
                <p>{message.content}</p>
                {message.response?.sources?.length ? (
                  <div className="mt-3 space-y-2">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Sources
                    </h3>
                    <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                      {message.response.sources.map((source: AskSource, index) => (
                        <li
                          key={`${message.id}-source-${index}`}
                          className="flex items-start gap-2"
                        >
                          <span
                            className="mt-0.5 inline-flex h-2 w-2 flex-none rounded-full bg-indigo-500"
                            aria-hidden="true"
                          />
                          <span>
                            {source.path}
                            {typeof source.page === "number" ? ` - page ${source.page}` : ""}
                            {source.heading ? ` - ${source.heading}` : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {message.response ? (
                  <footer className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                    <span>Confidence: {formatConfidence(message.response.confidence)}</span>
                    <span>
                      Escalate:{" "}
                      {message.response.should_escalate ? (
                        <span className="font-semibold text-rose-600">Yes</span>
                      ) : (
                        "No"
                      )}
                    </span>
                    <span className="truncate">Request ID: {message.response.request_id}</span>
                  </footer>
                ) : null}
                {message.status === "error" ? (
                  <p className="mt-2 text-xs text-rose-600">
                    {error ?? "Try asking again in a few minutes."}
                  </p>
                ) : null}
              </div>
            </article>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="mt-6 rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/70"
        >
          <div className="flex items-end gap-3">
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <Paperclip className="h-5 w-5" aria-hidden="true" />
              <span className="sr-only">Attach file</span>
            </button>
            <div className="flex-1">
              <label htmlFor="chat-message" className="sr-only">
                Message Atticus
              </label>
              <textarea
                id="chat-message"
                value={composer}
                onChange={(event) => setComposer(event.target.value)}
                rows={3}
                placeholder="Message Atticus…"
                className="max-h-[160px] min-h-[72px] w-full resize-y rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-300 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-100 dark:focus:border-indigo-500 dark:focus:ring-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={isStreaming || !composer.trim()}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-400"
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              ) : (
                <Send className="h-4 w-4" aria-hidden="true" />
              )}
              <span>{isStreaming ? "Sending…" : "Send"}</span>
            </button>
          </div>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex flex-wrap gap-3">
              {shortcuts.map((shortcut) => (
                <span
                  key={shortcut.label}
                  className="rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600 dark:bg-slate-800/60 dark:text-slate-300"
                >
                  {shortcut.label} · {shortcut.description}
                </span>
              ))}
            </div>
            {error ? (
              <span className="text-rose-600">{error}</span>
            ) : lastAssistant ? (
              <span className="truncate text-slate-400">
                Last request: {lastAssistant.request_id}
              </span>
            ) : null}
          </div>
        </form>
      </div>

      <aside className="flex flex-col gap-6">
        {highlights.map((item) => (
          <article
            key={item.title}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{item.title}</h3>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{item.description}</p>
          </article>
        ))}
      </aside>
    </section>
  );
}

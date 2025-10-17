"use client";

import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import { streamAsk, type AskStreamEvent } from "@/lib/ask-client";
import type { AskResponse, AskSource } from "@/lib/ask-contract";
import AnswerRenderer from "@/components/AnswerRenderer";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "pending" | "complete" | "error";
  response?: AskResponse;
  error?: string;
  question?: string;
}

function createId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function formatConfidence(confidence: number | null | undefined) {
  if (confidence === null || confidence === undefined || Number.isNaN(confidence)) {
    return "—";
  }
  return `${Math.round(confidence * 100)}%`;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [composer, setComposer] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showIntro, setShowIntro] = useState(true);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = composer.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    setError(null);
    if (showIntro) {
      setShowIntro(false);
    }

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
      content: "Atticus is thinking...",
      question: trimmed,
    };

    setMessages((prev) => [...prev, userMessage, placeholder]);
    setComposer("");
    setIsStreaming(true);

    try {
      await streamAsk(
        { question: trimmed, filters: undefined, contextHints: undefined, topK: undefined, models: undefined },
        {
          onEvent: (event: AskStreamEvent) => {
            if (event.type === "answer") {
              const response = event.payload;
              setMessages((prev) =>
                prev.map((message) =>
                  message.id === placeholder.id
                    ? {
                        ...message,
                        status: "complete",
                        content: response.answer ?? response.clarification?.message ?? "",
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

  async function handleClarificationChoice(messageId: string, models: string[]) {
    if (!models.length || isStreaming) {
      return;
    }
    const target = messages.find((message) => message.id === messageId);
    if (!target?.question) {
      return;
    }
    setError(null);
    if (showIntro) {
      setShowIntro(false);
    }
    setIsStreaming(true);
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? {
              ...message,
              status: "pending",
              content: "Atticus is thinking...",
              response: message.response ? { ...message.response, clarification: undefined } : message.response,
            }
          : message
      )
    );

    try {
      await streamAsk(
        {
          question: target.question,
          models,
          filters: undefined,
          contextHints: undefined,
          topK: undefined,
        },
        {
          onEvent: (event: AskStreamEvent) => {
            if (event.type === "answer") {
              const response = event.payload;
              setMessages((prev) =>
                prev.map((message) =>
                  message.id === messageId
                    ? {
                        ...message,
                        status: "complete",
                        content: response.answer ?? response.clarification?.message ?? "",
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
      const messageError = err instanceof Error ? err.message : "Something went wrong.";
      setError(messageError);
      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? {
                ...message,
                status: "error",
                content: "Unable to generate a response. Try again in a few moments.",
                error: messageError,
              }
            : message
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <section className="flex h-full min-h-0 flex-1 flex-col">
      <div className="flex-1 min-h-0 overflow-y-auto px-4 pb-6 pt-6 sm:px-6 lg:px-8 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {showIntro && messages.length === 0 ? (
          <div className="flex h-full min-h-full items-center justify-center text-center">
            <div className="max-w-xl space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.35em] text-slate-400 dark:text-slate-500">
                Welcome
              </p>
              <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
                Hi there — I’m Atticus.
              </h2>
              <p className="text-base text-slate-600 dark:text-slate-300">
                Ask me about any FUJIFILM product, process, or spec. Every answer comes sourced
                from verified documentation.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex min-h-full flex-col justify-end gap-4">
            {messages.map((message) => (
              <article
                key={message.id}
                className={
                  message.role === "assistant" ? "flex justify-start" : "flex justify-end"
                }
              >
                <div
                  className={
                    message.role === "assistant"
                      ? "max-w-3xl rounded-2xl bg-slate-100 p-4 text-sm text-slate-800 shadow dark:bg-slate-900 dark:text-slate-200"
                      : "max-w-3xl rounded-2xl bg-slate-900 p-4 text-sm text-white shadow dark:bg-slate-100 dark:text-slate-900"
                  }
                >
                  {message.role === "assistant" ? (
                    <AnswerRenderer
                      text={message.content}
                      response={message.response}
                      disabled={isStreaming}
                      onClarify={(models) => handleClarificationChoice(message.id, models)}
                    />
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                  {message.response?.sources?.length ? (
                    <div className="mt-3 space-y-1 text-xs text-slate-600 dark:text-slate-400">
                      <p className="font-semibold uppercase tracking-wide">Sources</p>
                      <ul className="space-y-1">
                        {message.response.sources.map((source: AskSource, index) => (
                          <li key={`${message.id}-source-${index}`}>
                            {source.path}
                            {typeof source.page === "number" ? ` · page ${source.page}` : ""}
                            {source.heading ? ` · ${source.heading}` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {message.response ? (
                    <footer className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
                      <span>Confidence: {formatConfidence(message.response.confidence)}</span>
                      <span>
                        Escalate:{" "}
                        {message.response.should_escalate === undefined
                          ? "-"
                          : message.response.should_escalate
                          ? "Yes"
                          : "No"}
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
        )}
      </div>
      <div className="shrink-0 px-4 pb-4 pt-4 sm:px-6 lg:px-8">
        <form
          onSubmit={handleSubmit}
          className="flex gap-3 rounded-2xl border border-slate-200 bg-white/95 p-4 shadow-lg backdrop-blur supports-[backdrop-filter]:backdrop-blur dark:border-slate-800 dark:bg-slate-950/90"
        >
          <div className="min-w-0 flex-1">
            <label htmlFor="chat-message" className="sr-only">
              Message Atticus
            </label>
            <Textarea
              id="chat-message"
              value={composer}
              onChange={(event) => setComposer(event.target.value)}
              rows={3}
              placeholder="Message Atticus..."
              className="max-h-[160px] min-h-[72px]"
            />
          </div>
          <Button type="submit" disabled={isStreaming || !composer.trim()} className="self-end rounded-xl">
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span>{isStreaming ? "Sending..." : "Send"}</span>
          </Button>
        </form>
        {error ? (
          <p className="mt-3 text-sm text-rose-600" role="status">
            {error}
          </p>
        ) : null}
      </div>
    </section>
  );
}

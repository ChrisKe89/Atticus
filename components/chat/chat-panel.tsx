"use client";

import { useMemo, useState } from "react";
import { Loader2, Paperclip, Send } from "lucide-react";
import { streamAsk, type AskStreamEvent } from "@/lib/ask-client";
import type { AskResponse, AskSource } from "@/lib/ask-contract";
import AnswerRenderer from "@/components/AnswerRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

const shortcuts = [
  { label: "Shift + Enter", description: "New line" },
  { label: "Ctrl + Enter", description: "Send message" },
  { label: "Esc", description: "Clear composer" },
];

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
    <section className="flex w-full justify-center">
      <Card className="flex w-full max-w-3xl flex-col">
        <CardHeader className="border-b border-slate-200/80 pb-4 dark:border-slate-800/60">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-base">Live conversation</CardTitle>
            <Badge variant={isStreaming ? "default" : "success"}>
              {isStreaming ? "Streaming..." : "Connected"}
            </Badge>
          </div>
          <CardDescription>
            Atticus shares grounded responses with request IDs and citation details for audit trails.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-4">
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
                    <div className="mt-3 space-y-2">
                      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                        Sources
                      </h3>
                      <ul className="space-y-1 text-xs text-slate-600 dark:text-slate-300">
                        {message.response.sources.map((source: AskSource, index) => (
                          <li key={`${message.id}-source-${index}`} className="flex items-start gap-2">
                            <span
                              className="mt-0.5 inline-flex h-2 w-2 flex-none rounded-full bg-indigo-500"
                              aria-hidden="true"
                            />
                            <span>
                              {source.path}
                              {typeof source.page === "number" ? ` · page ${source.page}` : ""}
                              {source.heading ? ` · ${source.heading}` : ""}
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
                        {message.response.should_escalate === undefined
                          ? "-"
                          : message.response.should_escalate ? (
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
        </CardContent>
        <CardFooter className="flex flex-col gap-3 border-t border-slate-200/80 bg-white/80 dark:border-slate-800/70 dark:bg-slate-950/60">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="flex items-end gap-3">
              <Button type="button" variant="outline" size="icon" className="rounded-2xl">
                <Paperclip className="h-5 w-5" aria-hidden="true" />
                <span className="sr-only">Attach file</span>
              </Button>
              <div className="flex-1">
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
              <Button type="submit" disabled={isStreaming || !composer.trim()} className="rounded-2xl">
                {isStreaming ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="h-4 w-4" aria-hidden="true" />
                )}
                <span>{isStreaming ? "Sending..." : "Send"}</span>
              </Button>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex flex-wrap gap-2">
                {shortcuts.map((shortcut) => (
                  <Badge key={shortcut.label} variant="subtle" className="normal-case">
                    {shortcut.label} · {shortcut.description}
                  </Badge>
                ))}
              </div>
              {error ? (
                <span className="text-rose-600">{error}</span>
              ) : lastAssistant ? (
                <span className="truncate text-slate-400">Last request: {lastAssistant.request_id}</span>
              ) : null}
            </div>
          </form>
        </CardFooter>
      </Card>
    </section>
  );
}



"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Send } from "lucide-react";

import type { AskResponse } from "@/lib/ask-contract";
import { createId } from "@/lib/id";

import AnswerRenderer from "@/components/AnswerRenderer";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAskStream } from "@/components/chat/use-ask-stream";

import type { ChatMessage, ChatSession } from "./types";

interface ChatPanelProps {
  session: ChatSession | null;
  onMessagesChange: (messages: ChatMessage[]) => void;
  disabled?: boolean;
}

export function ChatPanel({ session, onMessagesChange, disabled }: ChatPanelProps) {
  const FRIENDLY_VALIDATION_MSG =
    "There is no context to that question or it is not a proper question, please try again";
  const [messages, setMessages] = useState<ChatMessage[]>(session?.messages ?? []);
  const [composer, setComposer] = useState("");
  const {
    start: startAsk,
    isStreaming,
    error,
  } = useAskStream({
    friendlyErrorMessage: FRIENDLY_VALIDATION_MSG,
  });
  const [showIntro, setShowIntro] = useState(!session || session.messages.length === 0);
  const formRef = useRef<HTMLFormElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setMessages(session?.messages ?? []);
    setShowIntro(!session || session.messages.length === 0);
    setComposer("");
  }, [session]);

  useEffect(() => {
    if (!session) {
      return;
    }
    if (session.messages === messages) {
      return;
    }
    onMessagesChange(messages);
  }, [messages, session, onMessagesChange]);

  const isDisabled = disabled || !session;

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    const maxRows = 6;
    const style = window.getComputedStyle(el);
    const lineHeight = parseFloat(style.lineHeight || "20");
    const padding = parseFloat(style.paddingTop || "0") + parseFloat(style.paddingBottom || "0");
    const border =
      parseFloat(style.borderTopWidth || "0") + parseFloat(style.borderBottomWidth || "0");
    const minHeight = Math.max(0, lineHeight * 3 + padding + border);
    const maxHeight = Math.max(minHeight, lineHeight * maxRows + padding + border);
    el.style.height = "auto";
    const newHeight = Math.min(el.scrollHeight, Math.floor(maxHeight));
    el.style.height = `${newHeight}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    autoResize();
  }, [composer]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) {
      return;
    }
    const trimmed = composer.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    if (showIntro) {
      setShowIntro(false);
    }

    const userMessage: ChatMessage = {
      id: createId("msg"),
      role: "user",
      status: "complete",
      content: trimmed,
    };
    const placeholder: ChatMessage = {
      id: createId("msg"),
      role: "assistant",
      status: "pending",
      content: "Atticus is thinking...",
      question: trimmed,
    };

    setMessages((prev) => [...prev, userMessage, placeholder]);
    setComposer("");

    await startAsk({
      question: trimmed,
      onAnswer: (response: AskResponse) => {
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
      },
      onError: ({ display, actual }) => {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === placeholder.id
              ? {
                  ...message,
                  status: "error",
                  content: display,
                  error: actual,
                }
              : message
          )
        );
      },
    });
  }

  async function handleClarificationChoice(messageId: string, models: string[]) {
    if (!session) {
      return;
    }
    if (!models.length || isStreaming) {
      return;
    }
    const target = messages.find((message) => message.id === messageId);
    if (!target?.question) {
      return;
    }
    if (showIntro) {
      setShowIntro(false);
    }
    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? {
              ...message,
              status: "pending",
              content: "Atticus is thinking...",
              response: message.response
                ? { ...message.response, clarification: undefined }
                : message.response,
            }
          : message
      )
    );

    await startAsk({
      question: target.question,
      models,
      onAnswer: (response: AskResponse) => {
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
      },
      onError: ({ display, actual }) => {
        setMessages((prev) =>
          prev.map((message) =>
            message.id === messageId
              ? {
                  ...message,
                  status: "error",
                  content: display,
                  error: actual,
                }
              : message
          )
        );
      },
    });
  }

  return (
    <section className="flex h-full min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-6 pt-6 [-ms-overflow-style:none] [scrollbar-width:none] sm:px-6 lg:px-8 [&::-webkit-scrollbar]:hidden">
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
                Ask me about any FUJIFILM product, process, or spec. Every answer comes sourced from
                verified documentation.
              </p>
            </div>
          </div>
        ) : (
          <div className="flex min-h-full flex-col justify-end gap-4">
            {messages.map((message) => (
              <article
                key={message.id}
                className={message.role === "assistant" ? "flex justify-start" : "flex justify-end"}
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
                      disabled={isStreaming || isDisabled}
                      onClarify={(models) => handleClarificationChoice(message.id, models)}
                    />
                  ) : (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
      <div className="shrink-0 px-4 pb-4 pt-4 sm:px-6 lg:px-8">
        <form
          ref={formRef}
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
              ref={textareaRef}
              disabled={isStreaming || isDisabled}
              aria-disabled={isStreaming || isDisabled}
              aria-busy={isStreaming}
              onKeyDown={(event) => {
                const composing = (event.nativeEvent as unknown as { isComposing?: boolean }).isComposing;
                if (event.key === "Enter" && !event.shiftKey && !composing) {
                  event.preventDefault();
                  if (!isStreaming && !isDisabled && composer.trim()) {
                    formRef.current?.requestSubmit();
                  }
                }
              }}
              rows={3}
              placeholder={isDisabled ? "Loading chat history..." : "Message Atticus..."}
              className="min-h-[72px] resize-none overflow-y-hidden"
            />
          </div>
          <Button
            type="submit"
            disabled={isStreaming || !composer.trim() || isDisabled}
            className="self-end rounded-xl"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-4 w-4" aria-hidden="true" />
            )}
            <span aria-live="polite">{isStreaming ? "Sending..." : "Send"}</span>
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

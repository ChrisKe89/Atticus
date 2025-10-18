"use client";

import { useCallback, useState } from "react";

import { streamAsk, type AskStreamEvent } from "@/lib/ask-client";
import type { AskRequest, AskResponse } from "@/lib/ask-contract";

export interface AskErrorInfo {
  display: string;
  actual: string;
}

export interface StartAskOptions {
  question: string;
  models?: AskRequest["models"];
  filters?: AskRequest["filters"];
  contextHints?: AskRequest["contextHints"];
  topK?: AskRequest["topK"];
  onStart?: () => void;
  onEvent?: (event: AskStreamEvent) => void;
  onAnswer?: (response: AskResponse) => void;
  onError?: (error: AskErrorInfo) => void;
}

interface UseAskStreamConfig {
  friendlyErrorMessage: string;
}

export function useAskStream({ friendlyErrorMessage }: UseAskStreamConfig) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(
    async ({
      question,
      models,
      filters,
      contextHints,
      topK,
      onStart,
      onEvent,
      onAnswer,
      onError,
    }: StartAskOptions) => {
      if (isStreaming) {
        return;
      }

      const trimmedQuestion = question.trim();
      if (!trimmedQuestion) {
        return;
      }

      setError(null);
      setIsStreaming(true);
      onStart?.();

      try {
        await streamAsk(
          {
            question: trimmedQuestion,
            models,
            filters,
            contextHints,
            topK,
          },
          {
            onEvent: (event) => {
              onEvent?.(event);
              if (event.type === "answer") {
                onAnswer?.(event.payload);
              }
            },
          }
        );
      } catch (err) {
        const actual = err instanceof Error ? err.message : friendlyErrorMessage;
        const display = friendlyErrorMessage;
        if (actual === friendlyErrorMessage) {
          setError(null);
        } else {
          setError(actual);
        }
        onError?.({ display, actual });
      } finally {
        setIsStreaming(false);
      }
    },
    [friendlyErrorMessage, isStreaming]
  );

  const resetError = useCallback(() => setError(null), []);

  return { start, isStreaming, error, resetError };
}

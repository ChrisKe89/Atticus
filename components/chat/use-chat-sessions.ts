"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { createId } from "@/lib/id";

import type { ChatMessage, ChatSession } from "./types";

const STORAGE_KEY = "atticus.chat.sessions.v1";
const DEFAULT_TITLE = "New chat";

function sanitizeSessions(value: unknown): ChatSession[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map<ChatSession | null>((entry) => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const { id, title, createdAt, updatedAt, messages } = entry as Partial<ChatSession> & {
        messages?: ChatMessage[];
      };
      if (typeof id !== "string" || typeof createdAt !== "number" || typeof updatedAt !== "number") {
        return null;
      }
      if (!Array.isArray(messages)) {
        return null;
      }
      const sanitizedMessages = messages.filter((message): message is ChatMessage => {
        if (!message || typeof message !== "object") {
          return false;
        }
        return typeof message.id === "string" && (message.role === "user" || message.role === "assistant");
      });
      const sanitized: ChatSession = {
        id,
        title: typeof title === "string" ? title : undefined,
        createdAt,
        updatedAt,
        messages: sanitizedMessages,
      };
      return sanitized;
    })
    .filter((session): session is ChatSession => session !== null);
}

function deriveTitle(session: ChatSession): string {
  if (session.title && session.title.trim() && session.title !== DEFAULT_TITLE) {
    return session.title.trim();
  }
  const firstUserMessage = session.messages.find((message) => message.role === "user");
  if (!firstUserMessage) {
    return DEFAULT_TITLE;
  }
  const trimmed = firstUserMessage.content.trim();
  if (!trimmed) {
    return DEFAULT_TITLE;
  }
  return trimmed.length > 60 ? `${trimmed.slice(0, 57)}…` : trimmed;
}

function createSessionRecord(messages: ChatMessage[] = [], title?: string): ChatSession {
  const session: ChatSession = {
    id: createId("chat"),
    title: title?.trim() || DEFAULT_TITLE,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages,
  };
  session.title = deriveTitle(session);
  return session;
}

export function useChatSessions() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (isReady) {
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        const initialSession = createSessionRecord();
        setSessions([initialSession]);
        setActiveSessionId(initialSession.id);
        setIsReady(true);
        return;
      }
      const parsed = JSON.parse(raw) as unknown;
      const sanitized = sanitizeSessions(parsed);
      if (!sanitized.length) {
        const fallback = createSessionRecord();
        setSessions([fallback]);
        setActiveSessionId(fallback.id);
        setIsReady(true);
        return;
      }
      sanitized.sort((a, b) => b.updatedAt - a.updatedAt);
      setSessions(sanitized.map((session) => ({ ...session, title: deriveTitle(session) })));
      setActiveSessionId(sanitized[0]?.id ?? null);
    } catch (error) {
      console.error("Failed to load chat sessions", error);
      const fallback = createSessionRecord();
      setSessions([fallback]);
      setActiveSessionId(fallback.id);
    } finally {
      setIsReady(true);
    }
  }, [isReady]);

  useEffect(() => {
    if (!isReady || typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (error) {
      console.error("Failed to persist chat sessions", error);
    }
  }, [sessions, isReady]);

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? null,
    [sessions, activeSessionId]
  );

  const createSession = useCallback(() => {
    const session = createSessionRecord();
    setSessions((current) => [session, ...current]);
    setActiveSessionId(session.id);
    return session;
  }, []);

  const selectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
  }, []);

  const updateSessionMessages = useCallback((sessionId: string, messages: ChatMessage[]) => {
    setSessions((current) => {
      const index = current.findIndex((entry) => entry.id === sessionId);
      if (index === -1) {
        const id = sessionId || createId("chat");
        const session: ChatSession = {
          id,
          title: DEFAULT_TITLE,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages,
        };
        session.title = deriveTitle(session);
        return [session, ...current];
      }
      const next = [...current];
      const existing = next[index];
      const updated: ChatSession = {
        ...existing,
        messages,
        updatedAt: Date.now(),
      };
      updated.title = deriveTitle(updated);
      next[index] = updated;
      next.sort((a, b) => b.updatedAt - a.updatedAt);
      return next;
    });
    setActiveSessionId((currentId) => currentId ?? (sessionId || null));
  }, []);

  const renameSession = useCallback((sessionId: string, title: string) => {
    setSessions((current) => {
      const index = current.findIndex((entry) => entry.id === sessionId);
      if (index === -1) {
        return current;
      }
      const next = [...current];
      next[index] = {
        ...next[index],
        title: title.trim() || DEFAULT_TITLE,
        updatedAt: Date.now(),
      };
      next.sort((a, b) => b.updatedAt - a.updatedAt);
      return next;
    });
  }, []);

  return {
    isReady,
    sessions,
    activeSession,
    activeSessionId,
    selectSession,
    createSession,
    updateSessionMessages,
    renameSession,
  };
}

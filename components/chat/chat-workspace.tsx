"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/chat/chat-panel";

import { ChatSidebar } from "./chat-sidebar";
import { useChatSessions } from "./use-chat-sessions";

export function ChatWorkspace() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { isReady, sessions, activeSession, activeSessionId, selectSession, createSession, updateSessionMessages } =
    useChatSessions();

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (activeSession) {
      return;
    }
    createSession();
  }, [isReady, activeSession, createSession]);

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-0"
      style={{ top: "var(--topbar-h, 64px)" }}
      aria-label="Chat workspace"
    >
      <main className="flex h-full flex-col overflow-hidden">
        <div className="mx-auto flex h-full min-h-0 w-full max-w-6xl flex-1 flex-row">
          <ChatSidebar
            open={sidebarOpen}
            onToggle={() => setSidebarOpen((open) => !open)}
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={selectSession}
            onCreateSession={createSession}
          />
          <div className="flex min-h-0 flex-1 flex-col px-4 pb-4 pt-4 sm:px-6 lg:px-8">
            <ChatPanel
              session={activeSession}
              onMessagesChange={(messages) => {
                if (!activeSession?.id) {
                  return;
                }
                updateSessionMessages(activeSession.id, messages);
              }}
              disabled={!isReady}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

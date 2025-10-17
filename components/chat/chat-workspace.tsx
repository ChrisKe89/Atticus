"use client";

import { ChatPanel } from "@/components/chat/chat-panel";

export function ChatWorkspace() {
  return (
    <div
      className="fixed inset-x-0 bottom-0 z-0"
      style={{ top: "var(--topbar-h, 64px)" }}
      aria-label="Chat workspace"
    >
      <main className="flex h-full flex-col overflow-hidden">
        <div className="mx-auto flex h-full min-h-0 w-full max-w-5xl flex-1 flex-col px-4 pb-4 pt-4 sm:px-6 lg:px-8">
          <ChatPanel />
        </div>
      </main>
    </div>
  );
}

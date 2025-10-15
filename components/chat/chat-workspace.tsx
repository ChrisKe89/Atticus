"use client";

import { useState } from "react";
import { PageHeader } from "@/components/page-header";
import { ChatPanel } from "@/components/chat/chat-panel";
import { ChatSidebar } from "@/components/chat/chat-sidebar";

export function ChatWorkspace() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex min-h-[70vh] w-full overflow-hidden rounded-3xl border border-slate-800/70 bg-slate-950 text-slate-100 shadow-2xl shadow-slate-950/50">
      <ChatSidebar open={sidebarOpen} onToggle={() => setSidebarOpen((value) => !value)} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center gap-4 border-b border-slate-800/80 bg-slate-900/60 px-6 py-4 backdrop-blur">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/90 text-lg font-semibold text-slate-900">
            A
          </div>
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-[0.3em] text-blue-300/80">Atticus</span>
            <h1 className="text-lg font-semibold text-slate-100">
              Where should we begin today?
            </h1>
            <p className="text-xs text-slate-400">Temporary chat · responses stay private to you</p>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-8 sm:px-10">
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
            <PageHeader
              eyebrow="Workspace overview"
              title="Ask Atticus anything about your current opportunities."
              description="Upload supporting collateral, follow up on tricky RFP questions, or review the citations from your last answer. Atticus will cite every response and flag when you should escalate."
            />
            <div className="flex flex-1 flex-col">
              <ChatPanel />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

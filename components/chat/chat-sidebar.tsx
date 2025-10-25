"use client";

import type { ComponentType, SVGProps } from "react";
import {
  BookOpen,
  Clock,
  FolderPlus,
  Menu,
  MessageSquarePlus,
  Search,
  Settings,
  Sparkles,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { ChatSession } from "./types";

interface ChatSidebarProps {
  open: boolean;
  onToggle: () => void;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateSession: () => void;
}

interface SidebarItem {
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const workspaceActions: SidebarItem[] = [
  { label: "Search chats", icon: Search },
  { label: "Library", icon: BookOpen },
  { label: "Projects", icon: FolderPlus },
];

const automationActions: SidebarItem[] = [
  { label: "Automations", icon: Sparkles },
  { label: "Workspace settings", icon: Settings },
];

export function ChatSidebar({
  open,
  onToggle,
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateSession,
}: ChatSidebarProps) {
  const widthClass = open ? "w-72" : "w-20";

  return (
    <aside
      className={cn(
        "group/sidebar relative flex h-full shrink-0 flex-col border-r border-slate-800/80 bg-slate-900/80 backdrop-blur transition-[width] duration-300 ease-in-out",
        widthClass
      )}
      aria-label="Workspace sidebar"
    >
      <div className="flex items-center justify-between px-4 py-5">
        <div
          className={cn(
            "flex items-center gap-3 text-left",
            open ? "opacity-100" : "pointer-events-none opacity-0"
          )}
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500 font-semibold text-slate-900">
            C
          </div>
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-widest text-slate-400">Atticus</p>
            <p className="text-sm font-medium text-slate-100">Chat workspace</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggle}
          className="rounded-lg border border-slate-800/60 bg-slate-900/60 p-2 text-slate-200 transition hover:border-slate-700 hover:bg-slate-800/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60"
          aria-expanded={open}
          aria-label={open ? "Collapse sidebar" : "Expand sidebar"}
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      <div className="px-3">
        <Button
          type="button"
          variant="secondary"
          className="w-full justify-center gap-2"
          onClick={onCreateSession}
        >
          <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
          {open ? "New chat" : null}
        </Button>
      </div>

      <nav className="mt-6 flex-1 space-y-8 px-2">
        <SidebarSection title="Workspace" items={workspaceActions} open={open} />
        <ChatHistorySection
          open={open}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={onSelectSession}
        />
        <SidebarSection title="Automation" items={automationActions} open={open} />
      </nav>

      <div className="flex items-center gap-3 border-t border-slate-800/80 px-4 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 font-semibold text-slate-900">
          J
        </div>
        {open ? (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-100">Jordan Carter</p>
            <p className="truncate text-xs text-slate-400">AE • North America</p>
          </div>
        ) : null}
      </div>
    </aside>
  );
}

function SidebarSection({ title, items, open }: { title: string; items: SidebarItem[]; open: boolean }) {
  return (
    <div>
      <p
        className={cn(
          "px-3 text-xs font-semibold uppercase tracking-widest text-slate-500 transition-opacity",
          open ? "opacity-100" : "opacity-0"
        )}
      >
        {title}
      </p>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item.label}>
            <button
              type="button"
              title={item.label}
              className={cn(
                "flex w-full items-center rounded-xl px-3 py-2 text-sm font-medium text-slate-200 transition hover:bg-slate-800/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60",
                open ? "gap-3 justify-start" : "justify-center"
              )}
            >
              <item.icon className="h-4 w-4 flex-none" aria-hidden="true" />
              {open ? <span className="truncate">{item.label}</span> : null}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChatHistorySection({
  open,
  sessions,
  activeSessionId,
  onSelectSession,
}: {
  open: boolean;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
}) {
  if (!sessions.length) {
    return null;
  }
  return (
    <div>
      <p
        className={cn(
          "px-3 text-xs font-semibold uppercase tracking-widest text-slate-500 transition-opacity",
          open ? "opacity-100" : "opacity-0"
        )}
      >
        Recent chats
      </p>
      <ul className="mt-3 space-y-2">
        {sessions.map((session) => {
          const isActive = session.id === activeSessionId;
          return (
            <li key={session.id}>
              <button
                type="button"
                onClick={() => onSelectSession(session.id)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60",
                  isActive
                    ? "bg-slate-800/80 text-slate-100 shadow"
                    : "text-slate-300 hover:bg-slate-800/60",
                  open ? "justify-start" : "justify-center"
                )}
                title={session.title}
              >
                <Clock className="h-4 w-4 flex-none" aria-hidden="true" />
                {open ? (
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium">{session.title}</p>
                    <p className="truncate text-xs text-slate-400">
                      {new Date(session.updatedAt).toLocaleString()}
                    </p>
                  </div>
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import type { ReviewChat, SourceSummary } from "../lib/types";

type AlertState =
  | { type: "success"; message: string }
  | { type: "error"; message: string }
  | null;

interface ChatReviewBoardProps {
  initialChats: ReviewChat[];
}

const statusPalette: Record<string, string> = {
  pending_review: "#f97316",
  draft: "#3b82f6",
  rejected: "#ef4444",
  reviewed: "#10b981",
};

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) {
    return "Unknown timestamp";
  }
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function summarise(value: string | null | undefined): string {
  if (!value) {
    return "No answer captured yet.";
  }
  return value.length > 140 ? `${value.slice(0, 137)}…` : value;
}

export function ChatReviewBoard({ initialChats }: ChatReviewBoardProps) {
  const [chats, setChats] = useState<ReviewChat[]>(initialChats);
  const [selectedId, setSelectedId] = useState<string | null>(initialChats[0]?.id ?? null);
  const [drafts, setDrafts] = useState<Record<string, string>>(() =>
    initialChats.reduce<Record<string, string>>((acc, chat) => {
      acc[chat.id] = chat.answer ?? "";
      return acc;
    }, {})
  );
  const [alert, setAlert] = useState<AlertState>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedChat = useMemo(
    () => chats.find((chat) => chat.id === selectedId) ?? null,
    [chats, selectedId]
  );

  function updateDraft(chatId: string, value: string) {
    setDrafts((prev) => ({ ...prev, [chatId]: value }));
  }

  function clearAlertAfterDelay() {
    setTimeout(() => setAlert(null), 4000);
  }

  async function callAction(action: "approve" | "reject" | "save-draft") {
    if (!selectedChat) {
      return;
    }
    const draftAnswer = drafts[selectedChat.id]?.trim() ?? "";
    if (action !== "reject" && !draftAnswer) {
      setAlert({ type: "error", message: "Answer cannot be empty." });
      clearAlertAfterDelay();
      return;
    }

    setIsSubmitting(true);
    setAlert(null);
    try {
      const response = await fetch(`/api/chats/${selectedChat.id}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: selectedChat.question,
          answer: draftAnswer,
          topSources: selectedChat.topSources,
          requestId: selectedChat.requestId,
        }),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const detail = typeof payload.detail === "string" ? payload.detail : "Unexpected error.";
        throw new Error(detail);
      }

      if (action === "approve") {
        setChats((prev) => prev.filter((chat) => chat.id !== selectedChat.id));
        setDrafts((prev) => {
          const next = { ...prev };
          delete next[selectedChat.id];
          return next;
        });
        setAlert({ type: "success", message: "Chat approved and archived." });
        clearAlertAfterDelay();
        setSelectedId((prevId) => {
          if (prevId !== selectedChat.id) {
            return prevId;
          }
          const remaining = chats.filter((chat) => chat.id !== selectedChat.id);
          return remaining[0]?.id ?? null;
        });
      } else {
        setChats((prev) =>
          prev.map((chat) => {
            if (chat.id !== selectedChat.id) {
              return chat;
            }
            const nextStatus = action === "reject" ? "rejected" : "draft";
            return {
              ...chat,
              status: nextStatus,
              answer: draftAnswer || chat.answer,
            };
          })
        );
        setAlert({
          type: "success",
          message: action === "reject" ? "Chat marked as rejected." : "Draft saved for further editing.",
        });
        clearAlertAfterDelay();
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Request failed.";
      setAlert({ type: "error", message });
      clearAlertAfterDelay();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem", padding: "1.5rem" }}>
      <header style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 600, margin: 0 }}>Escalated Chats</h1>
        <p style={{ margin: 0, color: "#475569" }}>
          Review low-confidence answers, curate improved responses, and keep the Atticus corpus fresh.
        </p>
        {alert ? (
          <div
            style={{
              marginTop: "0.75rem",
              padding: "0.75rem 1rem",
              borderRadius: "0.75rem",
              backgroundColor: alert.type === "success" ? "#dcfce7" : "#fee2e2",
              color: alert.type === "success" ? "#166534" : "#991b1b",
              fontSize: "0.9rem",
            }}
          >
            {alert.message}
          </div>
        ) : null}
      </header>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(260px, 1fr) 2fr",
          gap: "1.5rem",
        }}
      >
        <aside
          style={{
            maxHeight: "calc(100vh - 180px)",
            overflowY: "auto",
            paddingRight: "0.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          {chats.length === 0 ? (
            <div
              style={{
                padding: "1.25rem",
                borderRadius: "1rem",
                border: "1px dashed #cbd5f5",
                background: "rgba(148, 163, 184, 0.1)",
                color: "#475569",
                fontSize: "0.95rem",
              }}
            >
              No escalations remaining. Fresh reviews will appear here automatically.
            </div>
          ) : (
            chats.map((chat) => {
              const isSelected = chat.id === selectedId;
              const badgeColor = statusPalette[chat.status] ?? "#64748b";
              return (
                <button
                  key={chat.id}
                  type="button"
                  onClick={() => setSelectedId(chat.id)}
                  style={{
                    textAlign: "left",
                    borderRadius: "1rem",
                    border: isSelected ? "2px solid #4f46e5" : "1px solid #e2e8f0",
                    backgroundColor: isSelected ? "#eef2ff" : "#ffffff",
                    boxShadow: isSelected ? "0 10px 20px rgba(79, 70, 229, 0.15)" : "none",
                    padding: "1rem 1.15rem",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    transition: "transform 0.15s ease-in-out",
                    transform: isSelected ? "translateY(-2px)" : "none",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span
                      style={{
                        backgroundColor: badgeColor,
                        color: "#ffffff",
                        fontSize: "0.7rem",
                        padding: "0.15rem 0.6rem",
                        borderRadius: "999px",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      {chat.status.replace("_", " ")}
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "#64748b" }}>
                      {(chat.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                    <h2 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "#0f172a" }}>
                      {chat.question}
                    </h2>
                    <p style={{ margin: 0, fontSize: "0.85rem", color: "#475569" }}>
                      {summarise(chat.answer)}
                    </p>
                  </div>
                  <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>
                    Captured {formatTimestamp(chat.createdAt)}
                  </span>
                </button>
              );
            })
          )}
        </aside>
        <section
          style={{
            padding: "1.5rem",
            backgroundColor: "#fff",
            borderRadius: "1.5rem",
            border: "1px solid rgba(148, 163, 184, 0.25)",
            boxShadow: "0 20px 30px rgba(15, 23, 42, 0.08)",
            minHeight: "420px",
            display: "flex",
            flexDirection: "column",
            gap: "1.2rem",
          }}
        >
          {selectedChat ? (
            <>
              <header style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                <span style={{ fontSize: "0.75rem", color: "#6366f1", letterSpacing: "0.08em" }}>
                  Review Queue
                </span>
                <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 600 }}>{selectedChat.question}</h2>
                <p style={{ margin: 0, fontSize: "0.85rem", color: "#475569" }}>
                  Request {selectedChat.requestId ?? "N/A"} · {formatTimestamp(selectedChat.createdAt)}
                </p>
              </header>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <label htmlFor="answer-editor" style={{ fontWeight: 500, fontSize: "0.9rem" }}>
                  Curated answer
                </label>
                <textarea
                  id="answer-editor"
                  value={drafts[selectedChat.id] ?? ""}
                  onChange={(event) => updateDraft(selectedChat.id, event.target.value)}
                  rows={10}
                  style={{
                    width: "100%",
                    resize: "vertical",
                    fontSize: "0.95rem",
                    lineHeight: 1.5,
                    padding: "0.85rem 1rem",
                    borderRadius: "1rem",
                    border: "1px solid #cbd5f5",
                    backgroundColor: "#f8fafc",
                  }}
                  placeholder="Compose the final answer that should be filed and used for future responses."
                />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                <span style={{ fontWeight: 500, fontSize: "0.9rem" }}>Top sources</span>
                <div
                  style={{
                    display: "grid",
                    gap: "0.6rem",
                    maxHeight: "120px",
                    overflowY: "auto",
                  }}
                >
                  {selectedChat.topSources.length === 0 ? (
                    <div
                      style={{
                        padding: "0.75rem",
                        borderRadius: "0.9rem",
                        backgroundColor: "#f1f5f9",
                        color: "#475569",
                        fontSize: "0.85rem",
                      }}
                    >
                      No sources captured for this chat.
                    </div>
                  ) : (
                    selectedChat.topSources.map((source: SourceSummary, index: number) => (
                      <div
                        key={`${selectedChat.id}-source-${index}`}
                        style={{
                          padding: "0.85rem",
                          borderRadius: "1rem",
                          border: "1px solid rgba(148, 163, 184, 0.35)",
                          background: "#f8fafc",
                        }}
                      >
                        <p style={{ margin: 0, fontWeight: 500, color: "#1e293b" }}>{source.path}</p>
                        {source.heading ? (
                          <p style={{ margin: "0.35rem 0 0", fontSize: "0.8rem", color: "#475569" }}>
                            {source.heading}
                          </p>
                        ) : null}
                        <div
                          style={{
                            marginTop: "0.5rem",
                            display: "flex",
                            gap: "0.75rem",
                            fontSize: "0.75rem",
                            color: "#64748b",
                          }}
                        >
                          {source.page != null ? <span>Page {source.page}</span> : null}
                          {source.score != null ? <span>Score {(source.score * 100).toFixed(1)}%</span> : null}
                          {source.chunkId ? <span>Chunk {source.chunkId}</span> : null}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <footer
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => callAction("save-draft")}
                    disabled={isSubmitting}
                    style={{
                      padding: "0.65rem 1.1rem",
                      borderRadius: "999px",
                      border: "1px solid #4f46e5",
                      backgroundColor: "#eef2ff",
                      color: "#4f46e5",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Save Draft
                  </button>
                  <button
                    type="button"
                    onClick={() => callAction("approve")}
                    disabled={isSubmitting}
                    style={{
                      padding: "0.65rem 1.1rem",
                      borderRadius: "999px",
                      border: "none",
                      background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
                      color: "#ffffff",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => callAction("reject")}
                    disabled={isSubmitting}
                    style={{
                      padding: "0.65rem 1.1rem",
                      borderRadius: "999px",
                      border: "1px solid #ef4444",
                      backgroundColor: "#fef2f2",
                      color: "#b91c1c",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Reject
                  </button>
                </div>
                <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                  Actions sync with the primary Atticus workspace instantly.
                </span>
              </footer>
            </>
          ) : (
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#94a3b8",
                fontSize: "0.95rem",
              }}
            >
              Select a chat from the list to begin reviewing.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

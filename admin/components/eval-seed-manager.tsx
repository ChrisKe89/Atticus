"use client";

import type { CSSProperties } from "react";
import { useMemo, useState } from "react";

import type { EvalSeed } from "../lib/types";

type EditableSeed = {
  id: string;
  question: string;
  documentsText: string;
  expectedAnswer: string;
  notes: string;
};

interface EvalSeedManagerProps {
  initialSeeds: EvalSeed[];
}

type SaveState = "idle" | "saving" | "saved" | "error";

export function EvalSeedManager({ initialSeeds }: EvalSeedManagerProps) {
  const seedDrafts = useMemo<EditableSeed[]>(
    () =>
      initialSeeds.map((seed, index) => ({
        id: `${seed.question}-${index}`,
        question: seed.question,
        documentsText: seed.relevantDocuments.join("\n"),
        expectedAnswer: seed.expectedAnswer ?? "",
        notes: seed.notes ?? "",
      })),
    [initialSeeds]
  );

  const [seeds, setSeeds] = useState<EditableSeed[]>(seedDrafts);
  const [status, setStatus] = useState<SaveState>("idle");
  const [message, setMessage] = useState<string>("");

  function addSeed() {
    setSeeds((prev) => [
      ...prev,
      {
        id: `seed-${Date.now()}`,
        question: "",
        documentsText: "",
        expectedAnswer: "",
        notes: "",
      },
    ]);
  }

  function removeSeed(id: string) {
    setSeeds((prev) => prev.filter((seed) => seed.id !== id));
  }

  function updateSeed(id: string, patch: Partial<EditableSeed>) {
    setSeeds((prev) => prev.map((seed) => (seed.id === id ? { ...seed, ...patch } : seed)));
  }

  async function saveSeeds() {
    setStatus("saving");
    setMessage("");
    const payload = {
      seeds: seeds.map((seed) => ({
        question: seed.question.trim(),
        relevantDocuments: seed.documentsText
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean),
        expectedAnswer: seed.expectedAnswer.trim() || null,
        notes: seed.notes.trim() || null,
      })),
    };

    const response = await fetch("/api/eval-seeds", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : "Unable to save evaluation seeds.";
      setStatus("error");
      setMessage(detail);
      return;
    }
    setStatus("saved");
    setMessage("Evaluation seeds updated.");
    setTimeout(() => setStatus("idle"), 3000);
  }

  return (
    <section
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: "1rem",
        padding: "1.5rem",
        background: "#ffffff",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
        <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Evaluation Seeds</h2>
        <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
          Curate gold-set questions and reference documents used by the evaluation harness.
        </p>
        {status === "error" ? (
          <span style={{ color: "#b91c1c", fontSize: "0.95rem" }}>{message}</span>
        ) : null}
        {status === "saved" ? (
          <span style={{ color: "#0f766e", fontSize: "0.95rem" }}>{message}</span>
        ) : null}
      </header>
      <div
        style={{
          display: "grid",
          gap: "1rem",
        }}
      >
        {seeds.map((seed) => (
          <article
            key={seed.id}
            style={{
              border: "1px solid #e2e8f0",
              borderRadius: "0.75rem",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.75rem",
            }}
          >
            <label style={labelStyle}>
              <span style={labelTitle}>Question</span>
              <textarea
                value={seed.question}
                onChange={(event) => updateSeed(seed.id, { question: event.target.value })}
                placeholder="What is the warm-up time of the Apeos C7070?"
                style={textareaStyle}
              />
            </label>
            <label style={labelStyle}>
              <span style={labelTitle}>Relevant documents</span>
              <textarea
                value={seed.documentsText}
                onChange={(event) => updateSeed(seed.id, { documentsText: event.target.value })}
                placeholder="content/ced/apeos-c7070.pdf"
                style={textareaStyle}
              />
              <span style={helperText}>One path per line; stored as CSV `relevant_documents` joined with semicolons.</span>
            </label>
            <label style={labelStyle}>
              <span style={labelTitle}>Expected answer (optional)</span>
              <textarea
                value={seed.expectedAnswer}
                onChange={(event) => updateSeed(seed.id, { expectedAnswer: event.target.value })}
                placeholder="The Apeos C7070 warms up in 30 seconds or less when embedded plug-ins are enabled."
                style={textareaStyle}
              />
            </label>
            <label style={labelStyle}>
              <span style={labelTitle}>Notes (optional)</span>
              <textarea
                value={seed.notes}
                onChange={(event) => updateSeed(seed.id, { notes: event.target.value })}
                placeholder="Double-check values with 2025 CED refresh."
                style={textareaStyle}
              />
            </label>
            <button
              type="button"
              onClick={() => removeSeed(seed.id)}
              style={{
                alignSelf: "flex-start",
                background: "#ef4444",
                color: "#ffffff",
                border: "none",
                borderRadius: "0.5rem",
                padding: "0.5rem 1.25rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Remove seed
            </button>
          </article>
        ))}
        <button
          type="button"
          onClick={addSeed}
          style={{
            alignSelf: "flex-start",
            background: "#1d4ed8",
            color: "#ffffff",
            border: "none",
            borderRadius: "0.75rem",
            padding: "0.6rem 1.4rem",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Add seed
        </button>
      </div>
      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button
          type="button"
          onClick={saveSeeds}
          disabled={status === "saving"}
          style={{
            background: "#15803d",
            color: "#ffffff",
            border: "none",
            borderRadius: "0.75rem",
            padding: "0.65rem 1.75rem",
            fontWeight: 600,
            cursor: status === "saving" ? "wait" : "pointer",
          }}
        >
          {status === "saving" ? "Saving…" : "Save seeds"}
        </button>
      </div>
    </section>
  );
}

const labelStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
};

const textareaStyle: CSSProperties = {
  minHeight: "72px",
  borderRadius: "0.75rem",
  border: "1px solid #cbd5f5",
  padding: "0.75rem",
  fontFamily: "ui-monospace, SFMono-Regular, SFMono, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
};

const labelTitle: CSSProperties = {
  fontWeight: 600,
};

const helperText: CSSProperties = {
  fontSize: "0.8rem",
  color: "#64748b",
};

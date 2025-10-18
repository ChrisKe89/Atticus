"use client";

import type { FormEvent } from "react";
import { useState } from "react";

type IngestSummary = {
  documents_processed: number;
  documents_skipped: number;
  chunks_indexed: number;
  elapsed_seconds: number;
  manifest_path: string;
  index_path: string;
  snapshot_path: string;
  ingested_at: string;
  embedding_model: string;
  embedding_model_version: string;
};

type PanelState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; summary: IngestSummary };

export function DocumentIngestionPanel() {
  const [fullRefresh, setFullRefresh] = useState(false);
  const [paths, setPaths] = useState("");
  const [state, setState] = useState<PanelState>({ status: "idle" });

  async function triggerIngestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ status: "loading" });
    const payload = {
      fullRefresh,
      paths: paths
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    };
    const response = await fetch("/api/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : "Unexpected ingestion failure.";
      setState({ status: "error", message: detail });
      return;
    }
    setState({ status: "success", summary: body as IngestSummary });
  }

  return (
    <section
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: "1rem",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        background: "#ffffff",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Embed New Documents</h2>
        <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
          Queue the ingestion pipeline to parse, chunk, and embed freshly updated sources.
        </p>
      </header>
      <form
        onSubmit={triggerIngestion}
        style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}
      >
        <label style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <span style={{ fontWeight: 600 }}>Content paths (optional)</span>
          <textarea
            value={paths}
            onChange={(event) => setPaths(event.target.value)}
            placeholder="content/ced/apeos-c8180.pdf\ncontent/ced/apeos-c7070.md"
            style={{
              minHeight: "96px",
              borderRadius: "0.75rem",
              border: "1px solid #cbd5f5",
              padding: "0.75rem",
              fontFamily: "ui-monospace, SFMono-Regular, SFMono, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
            }}
          />
          <span style={{ fontSize: "0.85rem", color: "#64748b" }}>
            Leave blank to re-embed the entire corpus using the active manifest.
          </span>
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={fullRefresh}
            onChange={(event) => setFullRefresh(event.target.checked)}
          />
          <span style={{ fontSize: "0.95rem" }}>Perform full refresh (ignore existing manifest)</span>
        </label>
        <button
          type="submit"
          disabled={state.status === "loading"}
          style={{
            alignSelf: "flex-start",
            background: "#2563eb",
            color: "#ffffff",
            border: "none",
            borderRadius: "0.75rem",
            padding: "0.65rem 1.5rem",
            fontWeight: 600,
            cursor: state.status === "loading" ? "wait" : "pointer",
          }}
        >
          {state.status === "loading" ? "Running…" : "Run ingestion"}
        </button>
      </form>
      {state.status === "error" ? (
        <div
          style={{
            borderRadius: "0.75rem",
            border: "1px solid #fecdd3",
            background: "#fef2f2",
            padding: "0.75rem 1rem",
            color: "#b91c1c",
            fontSize: "0.95rem",
          }}
        >
          {state.message}
        </div>
      ) : null}
      {state.status === "success" ? (
        <dl
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "0.75rem",
            margin: 0,
          }}
        >
          <SummaryItem label="Documents processed" value={state.summary.documents_processed} />
          <SummaryItem label="Documents skipped" value={state.summary.documents_skipped} />
          <SummaryItem label="Chunks indexed" value={state.summary.chunks_indexed} />
          <SummaryItem
            label="Elapsed (s)"
            value={state.summary.elapsed_seconds.toFixed(2)}
          />
          <SummaryItem label="Manifest" value={state.summary.manifest_path} />
          <SummaryItem label="Index" value={state.summary.index_path} />
          <SummaryItem label="Snapshot" value={state.summary.snapshot_path} />
          <SummaryItem label="Embedded at" value={state.summary.ingested_at} />
          <SummaryItem label="Embedding model" value={state.summary.embedding_model} />
          <SummaryItem label="Embedding version" value={state.summary.embedding_model_version} />
        </dl>
      ) : null}
    </section>
  );
}

function SummaryItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: "0.75rem",
        padding: "0.75rem",
        background: "#f8fafc",
      }}
    >
      <dt style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "#94a3b8" }}>{label}</dt>
      <dd style={{ margin: 0, fontWeight: 600, fontSize: "0.95rem", color: "#0f172a" }}>{value}</dd>
    </div>
  );
}

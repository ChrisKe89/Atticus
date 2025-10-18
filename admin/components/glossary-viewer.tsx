import type { CSSProperties } from "react";

import type { GlossaryEntry } from "../lib/types";

interface GlossaryViewerProps {
  entries: GlossaryEntry[];
}

export function GlossaryViewer({ entries }: GlossaryViewerProps) {
  if (entries.length === 0) {
    return (
      <section
        style={{
          border: "1px solid #e2e8f0",
          borderRadius: "1rem",
          padding: "1.5rem",
          background: "#ffffff",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", marginTop: 0 }}>Glossary Library</h2>
        <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
          No glossary entries found. Upload `indices/dictionary.json` or add entries via the FastAPI admin endpoint.
        </p>
      </section>
    );
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
        gap: "0.75rem",
      }}
    >
      <header>
        <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Glossary Library</h2>
        <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
          Review canonical terms, aliases, and synonyms surfaced to chat users when answers cite a glossary entry.
        </p>
      </header>
      <table
        style={{
          width: "100%",
          borderCollapse: "separate",
          borderSpacing: 0,
          border: "1px solid #e2e8f0",
          borderRadius: "0.75rem",
          overflow: "hidden",
        }}
      >
        <thead style={{ background: "#f8fafc" }}>
          <tr>
            <th style={headerCellStyle}>Term</th>
            <th style={headerCellStyle}>Synonyms</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.term}>
              <td style={cellStyle}>{entry.term}</td>
              <td style={cellStyle}>{entry.synonyms.join(", ") || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

const headerCellStyle: CSSProperties = {
  textAlign: "left",
  padding: "0.75rem 1rem",
  fontSize: "0.85rem",
  textTransform: "uppercase",
  color: "#64748b",
  borderBottom: "1px solid #e2e8f0",
};

const cellStyle: CSSProperties = {
  padding: "0.75rem 1rem",
  borderBottom: "1px solid #e2e8f0",
  fontSize: "0.95rem",
  color: "#0f172a",
  background: "#ffffff",
};

"use client";

import { useMemo, useState } from "react";
import type { CSSProperties, FormEvent } from "react";
import type { GlossaryEntry } from "../lib/types";

type AlertState = { type: "success" | "error"; message: string } | null;

type FormState = {
  term: string;
  definition: string;
  synonyms: string;
  aliases: string;
  units: string;
  productFamilies: string;
  status: string;
};

function normaliseGlossaryEntry(entry: Partial<GlossaryEntry>): GlossaryEntry {
  const term = typeof entry.term === "string" ? entry.term : "";
  const definition = typeof entry.definition === "string" ? entry.definition : "";
  const synonyms = Array.isArray(entry.synonyms) ? entry.synonyms.map(String) : [];
  const aliases = Array.isArray(entry.aliases) ? entry.aliases.map(String) : [];
  const units = Array.isArray(entry.units) ? entry.units.map(String) : [];
  const productFamilies = Array.isArray(entry.productFamilies)
    ? entry.productFamilies.map(String)
    : [];
  const status = typeof entry.status === "string" ? entry.status : "PENDING";
  const reviewNotes = typeof entry.reviewNotes === "string" ? entry.reviewNotes : null;
  return { term, definition, synonyms, aliases, units, productFamilies, status, reviewNotes };
}

function sortEntries(entries: GlossaryEntry[]): GlossaryEntry[] {
  return [...entries].sort((a, b) => a.term.localeCompare(b.term, undefined, { sensitivity: "base" }));
}

function parseList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

const defaultFormState: FormState = {
  term: "",
  definition: "",
  synonyms: "",
  aliases: "",
  units: "",
  productFamilies: "",
  status: "APPROVED",
};

export function GlossaryViewer({ entries }: { entries: GlossaryEntry[] }) {
  const initialEntries = useMemo(() => sortEntries(entries.map(normaliseGlossaryEntry)), [entries]);
  const [items, setItems] = useState<GlossaryEntry[]>(initialEntries);
  const [form, setForm] = useState<FormState>(defaultFormState);
  const [alert, setAlert] = useState<AlertState>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function showAlert(next: AlertState) {
    setAlert(next);
    if (next) {
      setTimeout(() => setAlert(null), 4000);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      term: form.term.trim(),
      definition: form.definition.trim(),
      synonyms: parseList(form.synonyms),
      aliases: parseList(form.aliases),
      units: parseList(form.units),
      productFamilies: parseList(form.productFamilies),
      status: form.status,
    };

    if (!payload.term || !payload.definition) {
      showAlert({ type: "error", message: "Both term and definition are required." });
      return;
    }

    setIsSubmitting(true);
    showAlert(null);

    try {
      const response = await fetch("/api/glossary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof (body as { detail?: unknown }).detail === "string"
          ? (body as { detail: string }).detail
          : "Unable to save glossary entry.";
        throw new Error(detail);
      }

      const entry = normaliseGlossaryEntry(body as Partial<GlossaryEntry>);
      setItems((prev) => sortEntries([...prev.filter((item) => item.term !== entry.term), entry]));
      setForm(defaultFormState);
      showAlert({ type: "success", message: `Saved glossary entry for ${entry.term}.` });
    } catch (error) {
      showAlert({
        type: "error",
        message: error instanceof Error ? error.message : "Unable to save glossary entry.",
      });
    } finally {
      setIsSubmitting(false);
    }
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
        gap: "1.5rem",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <h2 style={{ fontSize: "1.25rem", margin: 0 }}>Glossary Library</h2>
        <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
          Maintain canonical troubleshooting terms so the workspace can surface consistent definitions.
        </p>
        {alert ? (
          <div
            style={{
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

      <form
        onSubmit={handleSubmit}
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          alignItems: "start",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-term" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Term
          </label>
          <input
            id="glossary-term"
            type="text"
            value={form.term}
            onChange={(event) => updateForm("term", event.target.value)}
            placeholder="POPO"
            required
            style={inputStyle}
          />
        </div>
        <div style={{ gridColumn: "1 / -1", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-definition" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Definition
          </label>
          <textarea
            id="glossary-definition"
            value={form.definition}
            onChange={(event) => updateForm("definition", event.target.value)}
            placeholder="Power off, power on."
            rows={3}
            required
            style={{ ...inputStyle, minHeight: "96px", resize: "vertical" }}
          />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-synonyms" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Synonyms
          </label>
          <input
            id="glossary-synonyms"
            type="text"
            value={form.synonyms}
            onChange={(event) => updateForm("synonyms", event.target.value)}
            placeholder="Power cycle"
            style={inputStyle}
          />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-aliases" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Aliases
          </label>
          <input
            id="glossary-aliases"
            type="text"
            value={form.aliases}
            onChange={(event) => updateForm("aliases", event.target.value)}
            placeholder="Restart"
            style={inputStyle}
          />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-units" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Units
          </label>
          <input
            id="glossary-units"
            type="text"
            value={form.units}
            onChange={(event) => updateForm("units", event.target.value)}
            placeholder=""
            style={inputStyle}
          />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-families" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Product families
          </label>
          <input
            id="glossary-families"
            type="text"
            value={form.productFamilies}
            onChange={(event) => updateForm("productFamilies", event.target.value)}
            placeholder=""
            style={inputStyle}
          />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
          <label htmlFor="glossary-status" style={{ fontWeight: 600, fontSize: "0.9rem" }}>
            Status
          </label>
          <select
            id="glossary-status"
            value={form.status}
            onChange={(event) => updateForm("status", event.target.value)}
            style={{ ...inputStyle, height: "40px" }}
          >
            <option value="APPROVED">Approved</option>
            <option value="PENDING">Pending</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </div>
        <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}>
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              borderRadius: "999px",
              border: "none",
              background: "linear-gradient(135deg, #0ea5e9, #6366f1)",
              color: "#ffffff",
              fontWeight: 600,
              padding: "0.65rem 1.5rem",
              cursor: isSubmitting ? "wait" : "pointer",
              boxShadow: "0 10px 20px rgba(79, 70, 229, 0.2)",
            }}
          >
            {isSubmitting ? "Saving…" : "Add entry"}
          </button>
        </div>
      </form>

      <div style={{ display: "grid", gap: "1rem" }}>
        {items.length === 0 ? (
          <p style={{ margin: 0, color: "#475569", fontSize: "0.95rem" }}>
            No glossary entries found yet. Use the form above to create the first definition.
          </p>
        ) : (
          items.map((entry) => (
            <article
              key={entry.term}
              style={{
                border: "1px solid #e2e8f0",
                borderRadius: "0.9rem",
                padding: "1.1rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.6rem",
                background: "#f8fafc",
              }}
            >
              <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 600, color: "#0f172a" }}>{entry.term}</h3>
                <span
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                    color: "#1e3a8a",
                  }}
                >
                  {entry.status}
                </span>
              </header>
              <p style={{ margin: 0, color: "#1e293b", fontSize: "0.9rem" }}>{entry.definition}</p>
              <div
                style={{
                  display: "grid",
                  gap: "0.4rem",
                  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
                  fontSize: "0.8rem",
                  color: "#475569",
                }}
              >
                <GlossaryDetail label="Synonyms" value={entry.synonyms} />
                <GlossaryDetail label="Aliases" value={entry.aliases} />
                <GlossaryDetail label="Units" value={entry.units} />
                <GlossaryDetail label="Product families" value={entry.productFamilies} />
              </div>
              {entry.reviewNotes ? (
                <p style={{ margin: 0, fontSize: "0.8rem", color: "#64748b" }}>
                  Reviewer notes: {entry.reviewNotes}
                </p>
              ) : null}
            </article>
          ))
        )}
      </div>
    </section>
  );
}

function GlossaryDetail({ label, value }: { label: string; value: string[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
      <span style={{ fontWeight: 600, textTransform: "uppercase" }}>{label}</span>
      <span>{value.length ? value.join(", ") : "—"}</span>
    </div>
  );
}

const inputStyle: CSSProperties = {
  width: "100%",
  borderRadius: "0.75rem",
  border: "1px solid #cbd5f5",
  padding: "0.65rem 0.85rem",
  fontSize: "0.95rem",
  backgroundColor: "#f8fafc",
  color: "#0f172a",
};

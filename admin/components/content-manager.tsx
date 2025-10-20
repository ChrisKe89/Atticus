"use client";

import { useMemo, useRef, useState } from "react";
import type { ContentEntry } from "../lib/types";
import { formatTimestamp } from "../lib/datetime";

type AlertState =
  | { type: "success" | "error" | "info"; message: string }
  | null;

interface ContentManagerProps {
  initialPath: string;
  initialEntries: ContentEntry[];
}

function normalizePath(value: string): string {
  if (!value || value === "." || value === "/") {
    return ".";
  }
  return value.replace(/^\.\/+/, "").replace(/\\/g, "/");
}

export function ContentManager({ initialPath, initialEntries }: ContentManagerProps) {
  const [currentPath, setCurrentPath] = useState<string>(normalizePath(initialPath));
  const [entries, setEntries] = useState<ContentEntry[]>(initialEntries);
  const [alert, setAlert] = useState<AlertState>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isReingesting, setIsReingesting] = useState(false);
  const [ingestionLogs, setIngestionLogs] = useState<string[]>([]);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const breadcrumb = useMemo(() => {
    const normalized = normalizePath(currentPath);
    if (normalized === ".") {
      return [];
    }
    return normalized.split("/").filter(Boolean);
  }, [currentPath]);

  function pushAlert(next: AlertState) {
    setAlert(next);
    if (next && next.type !== "info") {
      setTimeout(() => setAlert(null), 4000);
    }
  }

  async function refresh(path: string) {
    setIsBusy(true);
    try {
      const normalized = normalizePath(path);
      const response = await fetch(`/api/content/list?path=${encodeURIComponent(normalized)}`, {
        method: "GET",
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = typeof payload.error === "string" ? payload.error : "Unable to load directory.";
        throw new Error(message);
      }
      const nextEntries = Array.isArray(payload.entries) ? payload.entries : [];
      setEntries(
        nextEntries.map((entry: Record<string, unknown>) => ({
          name: String(entry.name ?? ""),
          path: String(entry.path ?? ""),
          type: entry.type === "directory" ? "directory" : "file",
          size: typeof entry.size === "number" ? entry.size : 0,
          modified: typeof entry.modified === "string" ? entry.modified : new Date().toISOString(),
        }))
      );
      setCurrentPath(normalized);
    } catch (error) {
      pushAlert({
        type: "error",
        message: error instanceof Error ? error.message : "Unable to load directory.",
      });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleBreadcrumb(index: number) {
    if (index < 0) {
      await refresh(".");
      return;
    }
    const target = breadcrumb.slice(0, index + 1).join("/") || ".";
    await refresh(target);
  }

  async function handleNavigate(entry: ContentEntry) {
    if (entry.type !== "directory") {
      return;
    }
    await refresh(entry.path);
  }

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) {
      return;
    }
    setIsBusy(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.set("path", currentPath);
        formData.set("file", file);
        const response = await fetch("/api/content/upload", {
          method: "POST",
          body: formData,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          const message = typeof payload.error === "string" ? payload.error : `Failed to upload ${file.name}.`;
          throw new Error(message);
        }
      }
      pushAlert({ type: "success", message: "Upload complete." });
      await refresh(currentPath);
    } catch (error) {
      pushAlert({
        type: "error",
        message: error instanceof Error ? error.message : "File upload failed.",
      });
    } finally {
      setIsBusy(false);
      setTimeout(() => {
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }, 0);
    }
  }

  async function handleCreateFolder() {
    const folderName = window.prompt("Folder name");
    if (!folderName) {
      return;
    }
    setIsBusy(true);
    try {
      const response = await fetch("/api/content/folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parentPath: currentPath, folderName }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = typeof payload.error === "string" ? payload.error : "Unable to create folder.";
        throw new Error(message);
      }
      pushAlert({ type: "success", message: `Folder "${folderName}" created.` });
      await refresh(currentPath);
    } catch (error) {
      pushAlert({
        type: "error",
        message: error instanceof Error ? error.message : "Unable to create folder.",
      });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(entry: ContentEntry) {
    const confirmed = window.confirm(`Delete "${entry.name}"? This cannot be undone.`);
    if (!confirmed) {
      return;
    }
    setIsBusy(true);
    try {
      const response = await fetch("/api/content/entry", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: entry.path }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = typeof payload.error === "string" ? payload.error : "Unable to delete entry.";
        throw new Error(message);
      }
      pushAlert({ type: "success", message: `"${entry.name}" deleted.` });
      await refresh(currentPath);
    } catch (error) {
      pushAlert({
        type: "error",
        message: error instanceof Error ? error.message : "Deletion failed.",
      });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleReingest() {
    setIsReingesting(true);
    setIngestionLogs([]);
    setDocumentCount(null);
    try {
      const response = await fetch("/api/content/reingest", { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = typeof payload.error === "string" ? payload.error : "Re-ingest failed.";
        throw new Error(message);
      }
      const logs = Array.isArray(payload.logs) ? payload.logs.map((log: unknown) => String(log)) : [];
      setIngestionLogs(logs);
      setDocumentCount(typeof payload.documents === "number" ? payload.documents : null);
      pushAlert({ type: "success", message: "Re-ingest completed." });
    } catch (error) {
      pushAlert({
        type: "error",
        message: error instanceof Error ? error.message : "Re-ingest failed.",
      });
    } finally {
      setIsReingesting(false);
    }
  }

  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
        borderRadius: "1.5rem",
        border: "1px solid rgba(148, 163, 184, 0.35)",
        padding: "1.5rem",
        background: "#ffffff",
        boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "1.35rem", fontWeight: 600, color: "#0f172a" }}>
              Content workspace
            </h2>
            <p style={{ margin: "0.25rem 0 0", color: "#475569", fontSize: "0.95rem" }}>
              Manage the documents served to the chat surface. Edits apply instantly to the next ingestion run.
            </p>
          </div>
          <button
            type="button"
            onClick={() => refresh(currentPath)}
            disabled={isBusy}
            style={{
              borderRadius: "999px",
              border: "1px solid rgba(148, 163, 184, 0.6)",
              padding: "0.45rem 1rem",
              background: "transparent",
              color: "#1e293b",
              fontWeight: 600,
              cursor: isBusy ? "wait" : "pointer",
            }}
          >
            Refresh
          </button>
        </div>
        <nav style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.85rem" }}>
          <button
            type="button"
            onClick={() => handleBreadcrumb(-1)}
            style={{
              border: "none",
              background: "none",
              color: breadcrumb.length === 0 ? "#4338ca" : "#6366f1",
              fontWeight: breadcrumb.length === 0 ? 600 : 500,
              cursor: "pointer",
            }}
          >
            content
          </button>
          {breadcrumb.map((segment, index) => (
            <span key={`${segment}-${index}`} style={{ display: "inline-flex", alignItems: "center", gap: "0.75rem" }}>
              <span style={{ color: "#cbd5f5" }}>/</span>
              <button
                type="button"
                onClick={() => handleBreadcrumb(index)}
                style={{
                  border: "none",
                  background: "none",
                  color: index === breadcrumb.length - 1 ? "#4338ca" : "#6366f1",
                  fontWeight: index === breadcrumb.length - 1 ? 600 : 500,
                  cursor: "pointer",
                }}
              >
                {segment}
              </button>
            </span>
          ))}
        </nav>
        {alert ? (
          <div
            role="status"
            style={{
              borderRadius: "1rem",
              padding: "0.75rem 1rem",
              background:
                alert.type === "success"
                  ? "#ecfdf5"
                  : alert.type === "error"
                  ? "#fef2f2"
                  : "#f8fafc",
              border:
                alert.type === "success"
                  ? "1px solid rgba(52,211,153,0.4)"
                  : alert.type === "error"
                  ? "1px solid rgba(248,113,113,0.4)"
                  : "1px solid rgba(148,163,184,0.35)",
              color:
                alert.type === "success"
                  ? "#047857"
                  : alert.type === "error"
                  ? "#b91c1c"
                  : "#334155",
              fontSize: "0.9rem",
            }}
          >
            {alert.message}
          </div>
        ) : null}
      </header>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isBusy}
          style={{
            borderRadius: "999px",
            border: "none",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "#ffffff",
            padding: "0.55rem 1.4rem",
            fontWeight: 600,
            cursor: isBusy ? "wait" : "pointer",
          }}
        >
          Upload files
        </button>
        <button
          type="button"
          onClick={handleCreateFolder}
          disabled={isBusy}
          style={{
            borderRadius: "999px",
            border: "1px solid rgba(99, 102, 241, 0.35)",
            background: "rgba(129, 140, 248, 0.08)",
            color: "#4f46e5",
            padding: "0.55rem 1.4rem",
            fontWeight: 600,
            cursor: isBusy ? "wait" : "pointer",
          }}
        >
          New folder
        </button>
        <button
          type="button"
          onClick={handleReingest}
          disabled={isReingesting}
          style={{
            borderRadius: "999px",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            background: "rgba(16, 185, 129, 0.08)",
            color: "#047857",
            padding: "0.55rem 1.4rem",
            fontWeight: 600,
            cursor: isReingesting ? "wait" : "pointer",
          }}
        >
          Re-ingest content
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={(event) => handleUpload(event.target.files)}
        />
      </div>

      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "separate",
            borderSpacing: 0,
            borderRadius: "1.25rem",
            overflow: "hidden",
            border: "1px solid rgba(148, 163, 184, 0.35)",
          }}
        >
          <thead style={{ background: "#f8fafc" }}>
            <tr style={{ textAlign: "left", color: "#475569", fontSize: "0.75rem", textTransform: "uppercase" }}>
              <th style={{ padding: "0.75rem 1rem", fontWeight: 600 }}>Name</th>
              <th style={{ padding: "0.75rem 1rem", fontWeight: 600 }}>Type</th>
              <th style={{ padding: "0.75rem 1rem", fontWeight: 600 }}>Modified</th>
              <th style={{ padding: "0.75rem 1rem", fontWeight: 600 }}>Size</th>
              <th style={{ padding: "0.75rem 1rem", fontWeight: 600, textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: "1.5rem", textAlign: "center", color: "#64748b", fontSize: "0.95rem" }}>
                  {isBusy ? "Loading..." : "This directory is empty."}
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.path} style={{ borderTop: "1px solid rgba(226, 232, 240, 0.65)" }}>
                  <td style={{ padding: "0.75rem 1rem", fontWeight: 600, color: "#1e293b" }}>
                    {entry.type === "directory" ? (
                      <button
                        type="button"
                        onClick={() => handleNavigate(entry)}
                        style={{
                          border: "none",
                          background: "none",
                          color: "#4f46e5",
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        {entry.name}
                      </button>
                    ) : (
                      entry.name
                    )}
                  </td>
                  <td style={{ padding: "0.75rem 1rem", color: "#64748b", textTransform: "capitalize" }}>{entry.type}</td>
                  <td style={{ padding: "0.75rem 1rem", color: "#64748b" }}>
                    {formatTimestamp(entry.modified)}
                  </td>
                  <td style={{ padding: "0.75rem 1rem", color: "#64748b" }}>
                    {entry.type === "directory" ? "—" : `${(entry.size / 1024).toFixed(1)} KB`}
                  </td>
                  <td style={{ padding: "0.75rem 1rem", textAlign: "right" }}>
                    <button
                      type="button"
                      onClick={() => handleDelete(entry)}
                      style={{
                        borderRadius: "999px",
                        border: "1px solid rgba(248, 113, 113, 0.35)",
                        background: "rgba(254, 226, 226, 0.5)",
                        color: "#b91c1c",
                        padding: "0.35rem 0.9rem",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {(isReingesting || ingestionLogs.length > 0) && (
        <div
          style={{
            borderRadius: "1.25rem",
            border: "1px solid rgba(79, 70, 229, 0.25)",
            background: "rgba(79, 70, 229, 0.04)",
            padding: "1rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, fontSize: "0.95rem", fontWeight: 600, color: "#3730a3" }}>
              Ingestion logs
            </h3>
            {documentCount != null ? (
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: "#4338ca" }}>
                Indexed {documentCount} documents
              </span>
            ) : null}
          </div>
          <pre
            style={{
              margin: 0,
              maxHeight: "260px",
              overflowY: "auto",
              borderRadius: "0.85rem",
              background: "#0f172a",
              color: "#e2e8f0",
              padding: "1rem",
              fontSize: "0.75rem",
              lineHeight: 1.5,
            }}
          >
            {(ingestionLogs.length ? ingestionLogs : ["Ingestion running..."]).join("")}
          </pre>
        </div>
      )}
    </section>
  );
}

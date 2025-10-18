"use client";

import { useMemo, useRef, useState } from "react";
import type { ContentEntry } from "@/lib/content-manager";

type AlertState =
  | { type: "success"; message: string }
  | { type: "error"; message: string }
  | { type: "info"; message: string }
  | null;

interface ContentManagerProps {
  initialPath: string;
  initialEntries: ContentEntry[];
}

function normalisePath(path: string): string {
  if (!path || path === ".") {
    return ".";
  }
  return path.replace(/^\.\/+/, "").replace(/\\/g, "/");
}

export function ContentManager({ initialPath, initialEntries }: ContentManagerProps) {
  const [currentPath, setCurrentPath] = useState<string>(normalisePath(initialPath));
  const [entries, setEntries] = useState<ContentEntry[]>(initialEntries);
  const [alert, setAlert] = useState<AlertState>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [changesPending, setChangesPending] = useState(false);
  const [ingestionLogs, setIngestionLogs] = useState<string[]>([]);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const breadcrumb = useMemo(() => {
    const path = normalisePath(currentPath);
    if (path === ".") {
      return [];
    }
    return path.split("/").filter(Boolean);
  }, [currentPath]);

  function showAlert(state: AlertState) {
    setAlert(state);
    if (state && state.type !== "info") {
      setTimeout(() => setAlert(null), 4000);
    }
  }

  async function refresh(path: string) {
    setIsLoading(true);
    try {
      const target = normalisePath(path);
      const response = await fetch(
        `/api/admin/content/list?path=${encodeURIComponent(target === "." ? "." : target)}`
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = payload.error ?? "Unable to retrieve directory contents.";
        throw new Error(message);
      }
      const payload = (await response.json()) as { entries: ContentEntry[] };
      setEntries(payload.entries);
      setCurrentPath(target);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load directory.";
      showAlert({ type: "error", message });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleNavigate(entry: ContentEntry) {
    if (entry.type !== "directory") {
      return;
    }
    await refresh(entry.path);
  }

  async function handleBreadcrumb(index: number) {
    if (index < 0) {
      await refresh(".");
      return;
    }
    const target = breadcrumb.slice(0, index + 1).join("/");
    await refresh(target || ".");
  }

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) {
      return;
    }
    setIsLoading(true);
    try {
      for (const file of Array.from(files)) {
        const formData = new FormData();
        formData.set("path", currentPath);
        formData.set("file", file);
        const response = await fetch("/api/admin/content/upload", { method: "POST", body: formData });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const message = payload.error ?? `Failed to upload ${file.name}.`;
          throw new Error(message);
        }
      }
      await refresh(currentPath);
      setChangesPending(true);
      showAlert({ type: "success", message: "File upload complete." });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      showAlert({ type: "error", message });
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function handleCreateFolder() {
    const folderName = window.prompt("Folder name");
    if (!folderName) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch("/api/admin/content/folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parentPath: currentPath, folderName }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = payload.error ?? "Unable to create folder.";
        throw new Error(message);
      }
      await refresh(currentPath);
      setChangesPending(true);
      showAlert({ type: "success", message: `Created folder ${folderName}.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Folder creation failed.";
      showAlert({ type: "error", message });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(entry: ContentEntry) {
    const confirmed = window.confirm(`Delete ${entry.name}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch("/api/admin/content/entry", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: entry.path }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = payload.error ?? "Unable to delete entry.";
        throw new Error(message);
      }
      await refresh(currentPath);
      setChangesPending(true);
      showAlert({ type: "success", message: `${entry.name} deleted.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Delete failed.";
      showAlert({ type: "error", message });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleReingest() {
    setIsIngesting(true);
    setIngestionLogs([]);
    setDocumentCount(null);
    setAlert({ type: "info", message: "Ingestion in progress…" });
    try {
      const response = await fetch("/api/admin/content/reingest", { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = payload.error ?? "Ingestion failed.";
        throw new Error(message);
      }
      setIngestionLogs(Array.isArray(payload.logs) ? payload.logs : []);
      setDocumentCount(
        typeof payload.documents === "number" && Number.isFinite(payload.documents)
          ? payload.documents
          : null
      );
      setChangesPending(false);
      showAlert({
        type: "success",
        message:
          payload.documents != null
            ? `Ingestion complete. Indexed ${payload.documents} documents.`
            : "Ingestion complete.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Ingestion failed.";
      showAlert({ type: "error", message });
    } finally {
      setIsIngesting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <p className="text-sm uppercase tracking-[0.15em] text-indigo-500">Content pipeline</p>
        <h1 className="text-3xl font-bold text-slate-900">Content Manager</h1>
        <p className="text-slate-500">
          Upload Markdown, PDF, or text sources, organise folders, and trigger ingestion to refresh the Atticus
          retrieval index.
        </p>
        {alert ? (
          <div
            className={`rounded-xl px-4 py-3 text-sm ${
              alert.type === "success"
                ? "bg-emerald-50 text-emerald-700"
                : alert.type === "error"
                ? "bg-rose-50 text-rose-700"
                : "bg-indigo-50 text-indigo-700"
            }`}
          >
            {alert.message}
          </div>
        ) : null}
        {changesPending ? (
          <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
            <span>Content changed — run ingestion now?</span>
            <button
              type="button"
              onClick={handleReingest}
              disabled={isIngesting}
              className="rounded-full bg-amber-600 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white shadow-sm transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Re-ingest content
            </button>
          </div>
        ) : null}
      </header>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm backdrop-blur">
        <div className="flex flex-wrap items-center gap-3 text-sm font-medium text-slate-600">
          <button
            type="button"
            onClick={() => handleBreadcrumb(-1)}
            className="rounded-full border border-slate-200 px-3 py-1.5 transition hover:border-indigo-200 hover:text-indigo-600"
          >
            content
          </button>
          {breadcrumb.map((segment, index) => (
            <div key={segment} className="flex items-center gap-3">
              <span className="text-slate-300">/</span>
              <button
                type="button"
                onClick={() => handleBreadcrumb(index)}
                className="rounded-full border border-slate-200 px-3 py-1.5 transition hover:border-indigo-200 hover:text-indigo-600"
              >
                {segment}
              </button>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Upload files
          </button>
          <button
            type="button"
            onClick={handleCreateFolder}
            disabled={isLoading}
            className="rounded-full border border-indigo-200 px-4 py-2 text-sm font-semibold text-indigo-600 transition hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            New folder
          </button>
          <button
            type="button"
            onClick={() => refresh(currentPath)}
            disabled={isLoading}
            className="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Refresh
          </button>
          <button
            type="button"
            onClick={handleReingest}
            disabled={isIngesting}
            className="rounded-full border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-600 transition hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Re-ingest content
          </button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={(event) => handleUpload(event.target.files)}
          className="hidden"
        />
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Name
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Type
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Modified
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                Size
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {entries.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-sm text-slate-500">
                  {isLoading ? "Loading…" : "This directory is empty."}
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.path} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 text-sm font-medium text-slate-700">
                    {entry.type === "directory" ? (
                      <button
                        type="button"
                        className="flex items-center gap-2 text-indigo-600 hover:text-indigo-500"
                        onClick={() => handleNavigate(entry)}
                      >
                        <span className="inline-flex h-2 w-2 rounded-full bg-indigo-400"></span>
                        {entry.name}
                      </button>
                    ) : (
                      <span className="flex items-center gap-2">
                        <span className="inline-flex h-2 w-2 rounded-full bg-slate-300"></span>
                        {entry.name}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500 capitalize">{entry.type}</td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {new Date(entry.modified).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-500">
                    {entry.type === "directory" ? "--" : `${(entry.size / 1024).toFixed(1)} KB`}
                  </td>
                  <td className="px-4 py-3 text-right text-sm">
                    <button
                      type="button"
                      onClick={() => handleDelete(entry)}
                      className="rounded-full border border-rose-200 px-3 py-1 text-xs font-semibold text-rose-600 transition hover:bg-rose-50"
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

      {isIngesting || ingestionLogs.length > 0 ? (
        <div className="space-y-3 rounded-2xl border border-indigo-200 bg-white px-5 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-indigo-700">Ingestion logs</h2>
            {documentCount != null ? (
              <span className="text-xs font-semibold uppercase tracking-wide text-indigo-500">
                Indexed {documentCount} documents
              </span>
            ) : null}
          </div>
          <pre className="max-h-64 overflow-y-auto rounded-xl bg-slate-900/90 p-4 text-xs text-slate-100 shadow-inner">
            {(ingestionLogs.length ? ingestionLogs : ["Ingestion running…"]).join("")}
          </pre>
        </div>
      ) : null}
    </section>
  );
}

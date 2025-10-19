import { readdir, stat, mkdir, writeFile, rm, readFile } from "node:fs/promises";
import path from "node:path";

const CONTENT_ROOT = path.resolve(process.cwd(), "content");
const LOG_PATH = path.resolve(process.cwd(), "reports", "content-actions.log");

export type ContentEntry = {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number;
  modified: string;
};

function normalizeRelativePath(input: string | undefined): string {
  if (!input) {
    return ".";
  }
  const trimmed = input.trim();
  if (!trimmed || trimmed === "/") {
    return ".";
  }
  return trimmed.replace(/^\.\/+/, "").replace(/\\/g, "/");
}

export function resolveContentPath(relativePath: string | undefined): string {
  const normalized = normalizeRelativePath(relativePath);
  const resolved = path.resolve(CONTENT_ROOT, normalized);
  if (!resolved.startsWith(CONTENT_ROOT)) {
    throw new Error("Path escapes content root.");
  }
  return resolved;
}

export async function listContent(relativePath: string | undefined): Promise<ContentEntry[]> {
  const target = resolveContentPath(relativePath);
  const items = await readdir(target, { withFileTypes: true });
  const entries = await Promise.all(
    items.map(async (item) => {
      const absolute = path.join(target, item.name);
      const stats = await stat(absolute);
      return {
        name: item.name,
        path: path.relative(CONTENT_ROOT, absolute).replace(/\\/g, "/"),
        type: item.isDirectory() ? "directory" : "file",
        size: item.isDirectory() ? 0 : stats.size,
        modified: stats.mtime.toISOString(),
      } satisfies ContentEntry;
    })
  );

  return entries.sort((a, b) => {
    if (a.type !== b.type) {
      return a.type === "directory" ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });
}

export async function ensureFolder(parentPath: string | undefined, folderName: string): Promise<string> {
  if (!folderName.trim()) {
    throw new Error("Folder name is required.");
  }
  const parent = resolveContentPath(parentPath);
  const target = path.resolve(parent, folderName.trim());
  if (!target.startsWith(CONTENT_ROOT)) {
    throw new Error("Folder path escapes content root.");
  }
  await mkdir(target, { recursive: true });
  await logContentAction("create-folder", path.relative(CONTENT_ROOT, target));
  return path.relative(CONTENT_ROOT, target).replace(/\\/g, "/");
}

export async function saveFile(targetDir: string | undefined, fileName: string, contents: Buffer): Promise<string> {
  if (!fileName.trim()) {
    throw new Error("File name is required.");
  }
  const directory = resolveContentPath(targetDir);
  const destination = path.resolve(directory, fileName.trim());
  if (!destination.startsWith(CONTENT_ROOT)) {
    throw new Error("File path escapes content root.");
  }
  await mkdir(path.dirname(destination), { recursive: true });
  await writeFile(destination, contents);
  await logContentAction("upload-file", path.relative(CONTENT_ROOT, destination), `${contents.length} bytes`);
  return path.relative(CONTENT_ROOT, destination).replace(/\\/g, "/");
}

export async function deleteEntry(relativePath: string): Promise<void> {
  const target = resolveContentPath(relativePath);
  await rm(target, { recursive: true, force: true });
  await logContentAction("delete-entry", path.relative(CONTENT_ROOT, target));
}

export async function logContentAction(action: string, targetPath: string, detail?: string): Promise<void> {
  const timestamp = new Date().toISOString();
  const entry = {
    timestamp,
    action,
    target: targetPath,
    detail: detail ?? null,
  };
  try {
    await mkdir(path.dirname(LOG_PATH), { recursive: true });
    await writeFile(LOG_PATH, `${JSON.stringify(entry)}\n`, { encoding: "utf-8", flag: "a" });
  } catch {
    // Ignore logging failures.
  }
}

export async function readFilePreview(relativePath: string): Promise<string> {
  const target = resolveContentPath(relativePath);
  const buffer = await readFile(target, { encoding: "utf-8" });
  return buffer.slice(0, 2000);
}

export function getContentRoot(): string {
  return CONTENT_ROOT;
}

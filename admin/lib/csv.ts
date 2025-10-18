import { access, appendFile, mkdir, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import path from "node:path";
import type { SourceSummary } from "./types";

const CSV_HEADER = "timestamp,question,answer,model,reviewer\n";

function sanitizeValue(value: string): string {
  const cleaned = value.replace(/\r?\n+/g, " ").replace(/\s{2,}/g, " ").trim();
  return `"${cleaned.replace(/"/g, '""')}"`;
}

async function ensureCsvFile(filePath: string): Promise<void> {
  try {
    await access(filePath, constants.F_OK);
  } catch {
    await mkdir(path.dirname(filePath), { recursive: true });
    await writeFile(filePath, CSV_HEADER, { encoding: "utf-8" });
  }
}

export function deriveCsvTarget(sources: SourceSummary[]): { family: string; model: string } {
  for (const source of sources) {
    if (!source.path) {
      continue;
    }
    const normalized = source.path.replace(/\\/g, "/");
    const parts = normalized.split("/").filter(Boolean);
    const contentIndex = parts.findIndex((part) => part === "content");
    if (contentIndex === -1) {
      continue;
    }
    const family = parts[contentIndex + 1] ?? "general";
    const filePart = parts[parts.length - 1] ?? "answers";
    const model = filePart.replace(/\.[^/.]+$/, "") || "answers";
    return { family, model };
  }
  return { family: "general", model: "answers" };
}

export async function appendChatCsvRecord(params: {
  family: string;
  model: string;
  question: string;
  answer: string;
  reviewer: string;
}): Promise<string> {
  const { family, model, question, answer, reviewer } = params;
  const baseDir = path.resolve(process.cwd(), "..", "content", family);
  const filePath = path.join(baseDir, `${model}.csv`);
  await ensureCsvFile(filePath);

  const timestamp = new Date().toISOString();
  const row = [
    sanitizeValue(timestamp),
    sanitizeValue(question),
    sanitizeValue(answer),
    sanitizeValue(`${family}/${model}`),
    sanitizeValue(reviewer),
  ].join(",");

  await appendFile(filePath, `${row}\n`, { encoding: "utf-8" });
  return filePath;
}

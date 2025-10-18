import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

const REPORT_PATH = path.resolve(process.cwd(), "..", "reports", "phase2-errors.txt");

export async function logPhaseTwoError(message: string): Promise<void> {
  const entry = `[${new Date().toISOString()}] ${message}\n`;
  try {
    await mkdir(path.dirname(REPORT_PATH), { recursive: true });
    await appendFile(REPORT_PATH, entry, { encoding: "utf-8" });
  } catch {
    // Swallow logging errors to keep request handlers resilient.
  }
}

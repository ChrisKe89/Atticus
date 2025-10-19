import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

const REPORT_PATH = path.resolve(process.cwd(), "..", "reports", "phase2-errors.txt");

export async function logPhaseTwoError(message: string): Promise<void> {
  const entry = {
    timestamp: new Date().toISOString(),
    level: "error",
    event: "phase_two_error",
    message,
  };
  try {
    await mkdir(path.dirname(REPORT_PATH), { recursive: true });
    await appendFile(REPORT_PATH, `${JSON.stringify(entry)}\n`, { encoding: "utf-8" });
  } catch {
    // Swallow logging errors to keep request handlers resilient.
  }
}

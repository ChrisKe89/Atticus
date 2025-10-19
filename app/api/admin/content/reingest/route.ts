import { NextResponse } from "next/server";
import { spawn } from "node:child_process";
import path from "node:path";
import { logContentAction } from "@/lib/content-manager";

function runIngestion(): Promise<{ logs: string[]; code: number }> {
  return new Promise((resolve, reject) => {
    const logs: string[] = [];
    const processEnv = { ...process.env };
    const scriptPath = path.resolve(process.cwd(), "scripts", "ingest_cli.py");
    const proc = spawn("python", [scriptPath], {
      cwd: process.cwd(),
      env: processEnv,
    });

    proc.stdout.on("data", (chunk) => {
      logs.push(chunk.toString());
    });

    proc.stderr.on("data", (chunk) => {
      logs.push(`[stderr] ${chunk.toString()}`);
    });

    proc.on("error", (error) => {
      reject(error);
    });

    proc.on("close", (code) => {
      resolve({ logs, code: code ?? -1 });
    });
  });
}

function extractDocumentCount(logs: string[]): number | null {
  const joined = logs.join("\n");
  const match = joined.match(/Indexed\s+(\d+)\s+documents?/i);
  if (match && match[1]) {
    return Number.parseInt(match[1], 10);
  }
  return null;
}

export async function POST() {
  try {
    const { logs, code } = await runIngestion();
    const documents = extractDocumentCount(logs);
    await logContentAction("reingest", ".", `exit=${code}${documents != null ? ` docs=${documents}` : ""}`);

    if (code !== 0) {
      return NextResponse.json(
        { error: "Ingestion failed", logs, exitCode: code },
        { status: 500 }
      );
    }

    return NextResponse.json({
      ok: true,
      logs,
      exitCode: code,
      documents,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Ingestion process failed.";
    await logContentAction("reingest", ".", `error=${message}`);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}


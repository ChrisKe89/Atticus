#!/usr/bin/env node
/**
 * Cross-platform wrapper to run knip without failing the build when unused references are found.
 */
import { spawnSync } from "node:child_process";

const pnpmCmd = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
const result = spawnSync(pnpmCmd, ["exec", "knip", "--reporter", "compact"], {
  stdio: "inherit",
});

if (result.error) {
  console.error("[knip] failed to launch:", result.error);
} else if (result.status !== 0) {
  console.warn("[knip] exited with code", result.status, "- continuing (informational audit)");
}

process.exit(0);

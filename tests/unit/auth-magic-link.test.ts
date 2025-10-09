import fs from "node:fs/promises";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { __test } from "@/lib/auth";

const { defaultMailboxDir, resolveMailboxDir, persistMagicLink } = __test;

const envKey = "AUTH_DEBUG_MAILBOX_DIR";
const email = "fallbacktester@example.com";
const magicLink = "https://atticus.local/test-link";

async function cleanupMailboxFile() {
  const filePath = path.resolve(defaultMailboxDir, `${email}.txt`);
  try {
    await fs.unlink(filePath);
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw error;
    }
  }
}

describe("magic link mailbox resolution", () => {
  const originalEnv = process.env[envKey];

  beforeEach(async () => {
    await cleanupMailboxFile();
  });

  afterEach(async () => {
    if (originalEnv === undefined) {
      delete process.env[envKey];
    } else {
      process.env[envKey] = originalEnv;
    }
    await cleanupMailboxFile();
  });

  it("defaults to the fallback directory when env is unset", () => {
    delete process.env[envKey];
    expect(resolveMailboxDir()).toBe(defaultMailboxDir);
  });

  it("respects an explicitly configured directory", () => {
    process.env[envKey] = "./custom-mailbox";
    expect(resolveMailboxDir()).toBe("./custom-mailbox");
  });

  it("allows disabling persistence with an empty directory env", () => {
    process.env[envKey] = " ";
    expect(resolveMailboxDir()).toBeNull();
  });

  it("writes magic links to the fallback directory when env is unset", async () => {
    delete process.env[envKey];
    await persistMagicLink(email, magicLink);
    const filePath = path.resolve(defaultMailboxDir, `${email}.txt`);
    const contents = await fs.readFile(filePath, "utf-8");
    expect(contents).toContain(magicLink);
  });
});

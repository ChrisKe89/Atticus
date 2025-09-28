import { expect, test } from "@playwright/test";
import path from "node:path";
import fs from "node:fs/promises";

const mailboxDir = process.env.AUTH_DEBUG_MAILBOX_DIR ?? "./logs/mailbox";
const adminEmail = process.env.PLAYWRIGHT_ADMIN_EMAIL ?? "admin@atticus.local";

async function waitForMagicLink(email: string, timeoutMs = 15_000): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  const filePath = path.resolve(mailboxDir, `${email.toLowerCase()}.txt`);
  while (Date.now() < deadline) {
    try {
      const contents = await fs.readFile(filePath, "utf-8");
      const lines = contents
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      const last = lines.at(-1);
      if (last && last.startsWith("http")) {
        return last;
      }
    } catch (error) {
      // file might not exist yet
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Magic link for ${email} not found in ${mailboxDir}`);
}

test.describe.configure({ mode: "serial" });

test("redirects unauthenticated users away from admin dashboard", async ({ page }) => {
  const response = await page.goto("/admin");
  expect(response?.status()).toBeLessThan(500);
  await expect(page).toHaveURL(/\/signin/);
  await expect(page.getByRole("heading", { name: "Sign in to Atticus" })).toBeVisible();
});

test("allows admins to load the glossary panel after magic link sign-in", async ({ page }) => {
  await page.goto("/signin");
  await page.getByLabel("Work email").fill(adminEmail);
  await page.getByRole("button", { name: /magic link/i }).click();
  const magicLink = await waitForMagicLink(adminEmail);
  await page.goto(magicLink);
  await page.waitForURL("**/admin");
  await expect(page.getByRole("heading", { name: "Operations and governance" })).toBeVisible();
  await expect(page.getByText("Add glossary entry")).toBeVisible();
});

import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs/promises";

const mailboxDir = process.env.AUTH_DEBUG_MAILBOX_DIR ?? "./logs/mailbox";
const adminEmail = process.env.PLAYWRIGHT_ADMIN_EMAIL ?? "admin@atticus.local";
const reviewerEmail =
  process.env.PLAYWRIGHT_REVIEWER_EMAIL ?? "glossary.author@seed.atticus";

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

test.beforeEach(async ({ context }) => {
  await context.clearCookies();
});

async function signInWithMagicLink(page: Page, email: string) {
  await page.goto("/signin");
  await page.getByLabel("Work email").fill(email);
  await page.getByRole("button", { name: /magic link/i }).click();
  const magicLink = await waitForMagicLink(email);
  await page.goto(magicLink);
  await page.waitForLoadState("networkidle");
}

test("redirects unauthenticated users away from admin dashboard", async ({ page }) => {
  const response = await page.goto("/admin");
  expect(response?.status()).toBeLessThan(500);
  await expect(page).toHaveURL(/\/signin/);
  await expect(page.getByRole("heading", { name: "Sign in to Atticus" })).toBeVisible();
});

test("prevents reviewer accounts from loading admin-only surfaces", async ({ page }) => {
  await signInWithMagicLink(page, reviewerEmail);
  await page.goto("/admin");
  await expect(page).toHaveURL("/");

  const glossaryResponse = await page.request.get("/api/glossary");
  expect(glossaryResponse.status()).toBe(403);
  const payload = await glossaryResponse.json();
  expect(payload).toMatchObject({ error: "forbidden" });
});

test("allows admins to load the glossary panel after magic link sign-in", async ({ page }) => {
  await signInWithMagicLink(page, adminEmail);
  await page.waitForURL("**/admin");
  await expect(page.getByRole("heading", { name: "Operations and governance" })).toBeVisible();
  await expect(page.getByText("Add glossary entry")).toBeVisible();

  const newTerm = `Playwright QA ${Date.now()}`;
  await page.getByLabel("Term").fill(newTerm);
  await page.getByLabel("Definition").fill("Confidence gate coverage from Playwright");
  await page.getByLabel("Synonyms").fill("qa-term, reviewer-check");
  await page.getByLabel("Status").selectOption({ value: "PENDING" });
  await page.getByRole("button", { name: "Save entry" }).click();

  await expect(page.getByText("Entry created successfully.")).toBeVisible();
  const createdRow = page.locator("tr", { hasText: newTerm }).first();
  await expect(createdRow).toBeVisible();

  await createdRow.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByText("Entry deleted.")).toBeVisible();
  await expect(page.locator("tr", { hasText: newTerm })).toHaveCount(0);
});

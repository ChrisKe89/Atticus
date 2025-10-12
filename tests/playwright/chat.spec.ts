import { expect, test } from "@playwright/test";

const shouldRun = process.env.PLAYWRIGHT_CHAT_CLARIFICATION === "true";

test.describe("chat clarification flow", () => {
  test.skip(!shouldRun, "Enable by setting PLAYWRIGHT_CHAT_CLARIFICATION=true");

  test("prompts for model selection and completes follow-up", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("textbox", { name: /message/i }).fill("Can the printer handle glossy stock?");
    await page.getByRole("button", { name: /send/i }).click();

    const clarificationCard = page.getByRole("heading", { name: /Need a little more detail/i });
    await expect(clarificationCard).toBeVisible();

    await page.getByRole("button", { name: "Apeos C7070 range" }).click();
    await expect(page.getByText(/Apeos C7070/i)).toBeVisible();
    await expect(page.getByRole("heading", { name: /Sources/i })).toBeVisible();
  });
});

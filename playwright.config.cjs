const { defineConfig, devices } = require("@playwright/test");
const path = require("node:path");

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000";

module.exports = defineConfig({
  testDir: "tests/playwright",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL,
    trace: "on-first-retry",
    storageState: undefined,
  },
  reporter: [["list"], ["html", { outputFolder: "reports/playwright" }]],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  outputDir: path.join(__dirname, "reports/playwright-artifacts"),
});

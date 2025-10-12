const { defineConfig, devices } = require("@playwright/test");
const path = require("node:path");

// Align with NEXTAUTH_URL host to ensure cookies are same-origin
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

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
  // Use a non-interactive reporter to avoid starting an HTML server
  reporter: [["list"]],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname localhost --port 3000",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
  outputDir: path.join(__dirname, "reports/playwright-artifacts"),
});

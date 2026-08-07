import { defineConfig } from "@playwright/test";

/**
 * A port of its own, deliberately not 3000.
 *
 * `reuseExistingServer` would otherwise hand the suite whatever dev server the
 * developer already has running — including its sign-in gate — and the auth
 * override below would silently not apply.
 */
const TEST_PORT = Number(process.env.PLAYWRIGHT_PORT ?? 3100);

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  webServer: {
    command: `npx next dev -p ${TEST_PORT}`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    /**
     * Run the specs against the anonymous app.
     *
     * `authEnabled` is true as soon as either provider id is set (src/auth.ts),
     * and every spec drives the onboarding form, which a signed-out browser
     * never reaches once the gate is up. A checkout whose .env.local carries
     * real OAuth credentials — the normal state for anyone who has run the
     * signed-in flow — therefore fails the whole suite on "Public GitHub URL"
     * with no hint as to why.
     *
     * Only these two ids matter; clearing more would be cargo-culting. Process
     * env wins over .env.local in Next, so this needs no file changes and
     * leaves the developer's own credentials untouched.
     */
    env: {
      AUTH_GOOGLE_ID: "",
      AUTH_GITHUB_ID: "",
    },
  },
  use: {
    baseURL,
    headless: true,
    trace: "retain-on-failure",
  },
  reporter: [["list"]],
});

import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

const sseHeaders = {
  "Cache-Control": "no-cache",
  Connection: "keep-alive",
};

/**
 * Shaped like a real rollup: a hub everything imports, two leaves, and a
 * module with no chunk of its own. Truncated, so the "showing N of M" path is
 * exercised rather than assumed.
 */
const mapResponse = JSON.stringify({
  available: true,
  total_modules: 9,
  total_edges: 4,
  truncated: true,
  modules: [
    {
      symbol: "flask.app",
      label: "app",
      file_path: "src/flask/app.py",
      chunk_id: "chunk-app",
      symbol_count: 42,
      depends_on: 2,
      depended_on_by: 0,
    },
    {
      symbol: "flask.sessions",
      label: "sessions",
      file_path: "src/flask/sessions.py",
      chunk_id: "chunk-sessions",
      symbol_count: 11,
      depends_on: 0,
      depended_on_by: 1,
    },
    {
      // A real import target with no chunk — a namespace package. It must stay
      // on the map, and must not be given a file path it does not have.
      symbol: "flask.sansio",
      label: "sansio",
      file_path: null,
      chunk_id: null,
      symbol_count: 0,
      depends_on: 0,
      depended_on_by: 1,
    },
  ],
  edges: [
    { source: "flask.app", target: "flask.sessions" },
    { source: "flask.app", target: "flask.sansio" },
  ],
});

const emptyMap = JSON.stringify({
  available: false,
  modules: [],
  edges: [],
  total_modules: 0,
  total_edges: 0,
  truncated: false,
});

async function mockApi(page: import("@playwright/test").Page, mapBody: string) {
  let mapRequests = 0;
  await page.route(
    new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    async (route) => {
      const path = new URL(route.request().url()).pathname;
      const method = route.request().method();

      if (path.includes("/graph/modules")) {
        mapRequests += 1;
        return route.fulfill({ status: 200, contentType: "application/json", body: mapBody });
      }
      if (path.endsWith("/account/usage")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            free_repositories_remaining: 1,
            provider_connected: false,
            groq_connected: false,
            huggingface_connected: false,
            credential_storage: "account_bound",
          }),
        });
      }
      if (path.endsWith("/repos") && method === "POST") {
        return route.fulfill({
          status: 202,
          contentType: "application/json",
          body: JSON.stringify({ repo_id: "repo-123", status: "queued" }),
        });
      }
      if (path.includes("/repos/repo-123/status")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "ready", progress: 100 }),
        });
      }
      if (path.includes("/repos/repo-123/first-impression")) {
        return route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          headers: sseHeaders,
          body: 'event: first_impression\ndata: {"v":1,"text":"Flask looks routing-heavy."}\n\nevent: done\ndata: {"v":1}\n\n',
        });
      }
      if (path.endsWith("/me")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ session_id: "anon", authenticated: false }),
        });
      }
      if (path.endsWith("/tours") && method === "GET") {
        return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
      }
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    },
  );
  return () => mapRequests;
}

/** The map is repo-level, so it is reachable without asking anything. */
async function openRepo(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Open-source contributor" }).click();
  await page.getByRole("button", { name: "Analyze and ask" }).click();
  await expect(page.getByRole("heading", { name: "Ask this repository" })).toBeVisible({
    timeout: 15_000,
  });
}

test("the module map draws the repository's own dependencies", async ({ page }) => {
  const mapRequests = await mockApi(page, mapResponse);
  await openRepo(page);

  // Collapsed by default: a reader who never opens it pays for no request.
  await expect(page.getByText("sessions", { exact: true })).toBeHidden();
  expect(mapRequests()).toBe(0);

  await page.getByRole("button", { name: "Module map" }).click();

  await expect(page.getByText("app", { exact: true })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("sessions", { exact: true })).toBeVisible();
  await expect(page.getByText("sansio", { exact: true })).toBeVisible();
  expect(mapRequests()).toBe(1);

  // Scoping is stated, not silent.
  await expect(page.getByText(/Showing the 3 busiest of 9 modules/)).toBeVisible();
});

test("selecting a module shows what it holds, and never invents a path", async ({ page }) => {
  await mockApi(page, mapResponse);
  await openRepo(page);
  await page.getByRole("button", { name: "Module map" }).click();
  await expect(page.getByText("sessions", { exact: true })).toBeVisible({ timeout: 15_000 });

  await page.getByText("sessions", { exact: true }).click();
  await expect(page.getByText("flask.sessions", { exact: true })).toBeVisible();
  await expect(page.getByText("src/flask/sessions.py")).toBeVisible();

  // The namespace package has no chunk. It says so rather than showing a path.
  await page.getByText("sansio", { exact: true }).click();
  await expect(page.getByText("no indexed source")).toBeVisible();
});

test("a repo with no python graph says so rather than drawing an empty map", async ({ page }) => {
  await mockApi(page, emptyMap);
  await openRepo(page);
  await page.getByRole("button", { name: "Module map" }).click();

  await expect(page.getByText(/No module map for this repository/)).toBeVisible({
    timeout: 15_000,
  });
});

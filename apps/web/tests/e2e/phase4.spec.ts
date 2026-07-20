import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";

// The app reads NEXT_PUBLIC_API_BASE_URL from .env.local at build time.
// In dev, this is typically "http://localhost:8000" (direct to backend),
// while the test default fallback is "/api" (Next.js rewrite proxy).
// We must match whatever the running app actually uses.
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function apiRoute(path: string): string {
  if (apiBaseUrl.startsWith("http")) {
    // Absolute URL — use glob that matches the full URL
    return `${apiBaseUrl}${path}`;
  }
  // Relative path — match any origin
  return `**${apiBaseUrl}${path}`;
}

const sseHeaders = {
  "Cache-Control": "no-cache",
  "Connection": "keep-alive",
};

function tourStreamBody(): string {
  return [
    'event: section_start\ndata: {"event":"section_start","v":1,"order":0,"title":"Entry points"}\n\n',
    'event: token\ndata: {"event":"token","v":1,"text":"Start with the Flask app object."}\n\n',
    'event: claim\ndata: {"event":"claim","v":1,"id":"claim-1","text":"The Flask class is the main app entry.","refs":[{"file_path":"src/flask/app.py","start_line":1,"end_line":20,"symbol":"Flask"}],"status":"verified","retrieval_path":["vector_search:k=8"],"verifier_note":"Grounded against app.py."}\n\n',
    'event: section_end\ndata: {"event":"section_end","v":1,"order":0}\n\n',
    'event: done\ndata: {"event":"done","v":1}\n\n',
  ].join("");
}

const chunkResponse = JSON.stringify({
  chunk_id: "chunk-123",
  repo_id: "repo-123",
  ref: {
    file_path: "src/flask/app.py",
    start_line: 1,
    end_line: 20,
    symbol: "Flask",
  },
  content: "class Flask:\n    pass",
  summary: "Flask application object.",
});

test("phase 4 tour starts and shows synchronized viewer shell", async ({ page }) => {
  let tourStreamRequests = 0;

  // Single dispatcher that intercepts all requests to the API backend.
  // The app's .env.local sets NEXT_PUBLIC_API_BASE_URL=http://localhost:8000,
  // so client-side fetches go directly to the backend, not through /api/ rewrite.
  await page.route(new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();

    // /account/usage
    if (path.endsWith("/account/usage")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          free_repositories_remaining: 1,
          free_questions_remaining: 5,
          provider_connected: false,
          groq_connected: false,
          huggingface_connected: false,
          credential_storage: "session_only",
        }),
      });
    }

    // POST /repos
    if (path.endsWith("/repos") && method === "POST") {
      return route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({ repo_id: "repo-123", status: "queued" }),
      });
    }

    // /repos/repo-123/status
    if (path.includes("/repos/repo-123/status")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "ready", progress: 100 }),
      });
    }

    // /repos/repo-123/first-impression (EventSource)
    if (path.includes("/repos/repo-123/first-impression")) {
      return route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        headers: sseHeaders,
        body: [
          'event: first_impression\ndata: {"event":"first_impression","v":1,"text":"Flask looks routing-heavy."}\n\n',
          'event: done\ndata: {"event":"done","v":1}\n\n',
        ].join(""),
      });
    }

    // POST /tours (create tour)
    if (path.endsWith("/tours") && method === "POST") {
      return route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ tour_id: "tour-123", stream_url: "/tours/tour-123/stream" }),
      });
    }

    // /tours/tour-123/stream (SSE)
    if (path.includes("/tours/tour-123/stream")) {
      tourStreamRequests += 1;
      return route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        headers: sseHeaders,
        body: tourStreamBody(),
      });
    }

    // /chunks/* (code viewer content)
    if (path.includes("/chunks/")) {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: chunkResponse,
      });
    }

    // Anything else — let it through
    return route.fallback();
  });

  await page.goto("/");

  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Analyze" }).click();

  await expect(page.getByRole("heading", { name: "What do you need?" })).toBeVisible();

  await page.getByRole("button", { name: "Learn the codebase" }).click();
  await page.getByRole("button", { name: "Open guided tour" }).click();

  await expect(page.getByRole("heading", { name: "Guided repository tour" })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Synchronized Code Viewer")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("class Flask:")).toBeVisible({ timeout: 15_000 });

  await page.reload();

  await expect(page.getByRole("heading", { name: "Guided repository tour" })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("heading", { name: "Entry points" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("class Flask:")).toBeVisible({ timeout: 15_000 });
  expect(tourStreamRequests).toBeGreaterThanOrEqual(2);
});

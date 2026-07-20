import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

function apiRoute(path: string): string {
  return apiBaseUrl.startsWith("/") ? `**${apiBaseUrl}${path}` : `${apiBaseUrl}${path}`;
}

test("phase 4 tour starts and shows synchronized viewer shell", async ({ page }) => {
  let tourStreamRequests = 0;
  await page.route(apiRoute("/account/usage"), async (route) => {
    await route.fulfill({
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
  });
  await page.route(apiRoute("/repos"), async (route) => {
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ repo_id: "repo-123", status: "queued" }),
    });
  });
  await page.route(apiRoute("/repos/repo-123/status"), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ready", progress: 100 }),
    });
  });
  await page.route(apiRoute("/repos/repo-123/first-impression"), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: [
        'event: first_impression\ndata: {"v":1,"text":"Flask looks routing-heavy."}\n\n',
        'event: done\ndata: {"v":1}\n\n',
      ].join(""),
    });
  });
  await page.route(apiRoute("/tours"), async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ tour_id: "tour-123", stream_url: "/tours/tour-123/stream" }),
    });
  });
  await page.route(apiRoute("/tours/tour-123/stream"), async (route) => {
    tourStreamRequests += 1;
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: [
        'event: section_start\ndata: {"event":"section_start","v":1,"order":0,"title":"Entry points"}\n\n',
        'event: token\ndata: {"event":"token","v":1,"section_order":0,"text":"Start with the Flask app object."}\n\n',
        'event: claim\ndata: {"event":"claim","v":1,"section_order":0,"id":"claim-1","text":"The Flask class is the main app entry.","refs":[{"file_path":"src/flask/app.py","start_line":1,"end_line":20,"symbol":"Flask"}],"status":"verified","retrieval_path":["vector_search:k=8"],"verifier_note":"Grounded against app.py."}\n\n',
        'event: section_end\ndata: {"event":"section_end","v":1,"section_order":0,"summary":"Begin with the Flask class."}\n\n',
        'event: done\ndata: {"event":"done","v":1}\n\n',
      ].join(""),
    });
  });
  await page.route(apiRoute("/chunks/**"), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
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
      }),
    });
  });

  await page.goto("/");

  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Analyze" }).click();

  await expect(page.getByRole("heading", { name: "What do you need?" })).toBeVisible();

  await page.getByRole("button", { name: "Learn the codebase" }).click();
  await page.getByRole("button", { name: "Open guided tour" }).click();

  await expect(page.getByRole("heading", { name: "Guided repository tour" })).toBeVisible();
  await expect(page.getByText("Synchronized Code Viewer")).toBeVisible();
  await expect(page.getByText("class Flask:")).toBeVisible();

  await page.reload();

  await expect(page.getByRole("heading", { name: "Guided repository tour" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Entry points" })).toBeVisible();
  await expect(page.getByText("class Flask:")).toBeVisible();
  expect(tourStreamRequests).toBeGreaterThanOrEqual(2);
});

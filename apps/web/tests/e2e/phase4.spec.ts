import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

test("phase 4 tour starts and shows synchronized viewer shell", async ({ page }) => {
  await page.route(`${apiBaseUrl}/repos`, async (route) => {
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ repo_id: "repo-123", status: "queued" }),
    });
  });
  await page.route(`${apiBaseUrl}/repos/repo-123/status`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ready", progress: 100 }),
    });
  });
  await page.route(`${apiBaseUrl}/repos/repo-123/first-impression`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body: [
        'event: first_impression\ndata: {"v":1,"text":"Flask looks routing-heavy."}\n\n',
        'event: done\ndata: {"v":1}\n\n',
      ].join(""),
    });
  });
  await page.route(`${apiBaseUrl}/tours`, async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ tour_id: "tour-123", stream_url: "/tours/tour-123/stream" }),
    });
  });
  await page.route(`${apiBaseUrl}/tours/tour-123/stream`, async (route) => {
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
  await page.route(`${apiBaseUrl}/chunks/**`, async (route) => {
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

  await page.getByLabel("Repo URL").fill(repoUrl);
  await page.getByRole("button", { name: "Index And Continue" }).click();

  await expect(page.getByText("Why Are You Here?")).toBeVisible();

  await page.getByRole("button", { name: "I want to learn this codebase" }).click();
  await page.getByRole("button", { name: "Start Tour" }).click();

  await expect(page.getByText("Tour View")).toBeVisible();
  await expect(page.getByText("Synchronized Code Viewer")).toBeVisible();
});

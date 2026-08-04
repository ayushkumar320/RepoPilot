import { expect, test } from "@playwright/test";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";

// The app reads NEXT_PUBLIC_API_BASE_URL from .env.local at build time. The
// committed default is "/api" (the same-origin Next.js rewrite proxy in
// next.config.mjs) so the session cookie survives; we must match whatever the
// running app actually uses.
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

const sseHeaders = {
  "Cache-Control": "no-cache",
  Connection: "keep-alive",
};

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

function answerFor(persona: string): string {
  return JSON.stringify({
    answer: `Answered for ${persona}.`,
    claims: [
      {
        id: "claim-1",
        text: "The Flask class is the main app entry.",
        refs: [
          { file_path: "src/flask/app.py", start_line: 1, end_line: 20, symbol: "Flask" },
        ],
        status: "verified",
        verifier_note: "Grounded against app.py.",
        retrieval_path: ["vector_search:k=8"],
      },
    ],
    retrieval_path: ["vector_search:k=8"],
  });
}

test("paste a repo, pick a persona, and ask — no tour step in between", async ({ page }) => {
  // Captures what the app actually sent, so the test proves the persona
  // reaches the backend rather than merely rendering in the sidebar.
  const askedFramings: (string | null)[] = [];

  await page.route(
    new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;
      const method = route.request().method();

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
          body: [
            'event: first_impression\ndata: {"v":1,"text":"Flask looks routing-heavy."}\n\n',
            'event: done\ndata: {"v":1}\n\n',
          ].join(""),
        });
      }

      if (path.includes("/repos/repo-123/ask") && method === "POST") {
        const body = route.request().postDataJSON() as {
          intent_profile?: { audience_framing?: string | null } | null;
        };
        const framing = body.intent_profile?.audience_framing ?? null;
        askedFramings.push(framing);
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: answerFor(framing ?? "nobody"),
        });
      }

      if (path.includes("/chunks/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: chunkResponse,
        });
      }

      return route.fallback();
    },
  );

  await page.goto("/");

  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Open-source contributor" }).click();
  await page.getByRole("button", { name: "Analyze and ask" }).click();

  // One action gets us all the way to the ask surface — no "start tour" click.
  await expect(page.getByRole("heading", { name: "Ask this repository" })).toBeVisible({
    timeout: 15_000,
  });

  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Answered for a first-time outside contributor")).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText("class Flask:")).toBeVisible({ timeout: 15_000 });

  // Switch lens mid-session and re-ask: the same question must go out under a
  // different persona.
  await page.getByRole("button", { name: "Competitive analyst" }).click();
  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Answered for a product strategist")).toBeVisible({
    timeout: 15_000,
  });

  expect(askedFramings).toEqual([
    "a first-time outside contributor preparing a pull request",
    "a product strategist at a competing company",
  ]);
});

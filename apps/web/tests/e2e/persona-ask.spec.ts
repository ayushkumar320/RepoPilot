import { expect, test } from "@playwright/test";

import { askStreamBody, sseHeaders } from "./sse";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";

// The app reads NEXT_PUBLIC_API_BASE_URL from .env.local at build time. The
// committed default is "/api" (the same-origin Next.js rewrite proxy in
// next.config.mjs) so the session cookie survives; we must match whatever the
// running app actually uses.
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

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
  const savedQuestions: string[] = [];

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
        const answer = answerFor(framing ?? "nobody");
        if (path.endsWith("/stream")) {
          return route.fulfill({
            status: 200,
            contentType: "text/event-stream",
            headers: sseHeaders,
            body: askStreamBody(answer),
          });
        }
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: answer,
        });
      }

      // Tour history is write-through and never blocks the ask path, but it
      // must not fall through to the network either or the test depends on a
      // running API.
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

      if (path.endsWith("/tours") && method === "POST") {
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ tour_id: "tour-123" }),
        });
      }

      if (path.endsWith("/tours/tour-123/messages") && method === "POST") {
        savedQuestions.push(
          (route.request().postDataJSON() as { question: string }).question,
        );
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ ordinal: savedQuestions.length - 1 }),
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
  await expect(page.getByLabel("Ask this repository")).toBeVisible({
    timeout: 15_000,
  });

  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Answered for a first-time outside contributor")).toBeVisible({
    timeout: 15_000,
  });

  // Sources fold into a "Verified sources" disclosure; the citation lives
  // inside it.
  await page.locator("summary.claim-group-label").first().click();

  // The claim states where it came from. Opening that source is covered by
  // "a claim opens the code it cites" below; this test stays about persona
  // routing and only checks that the citation reached the DOM.
  await expect(page.getByText("src/flask/app.py:1-20")).toBeVisible({ timeout: 15_000 });

  // Switch lens mid-session and re-ask: the same question must go out under a
  // different persona.
  await page.getByLabel("Answering as").selectOption({ label: "Competitive analyst" });
  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Answered for a product strategist")).toBeVisible({
    timeout: 15_000,
  });

  expect(askedFramings).toEqual([
    "a first-time outside contributor preparing a pull request",
    "a product strategist at a competing company",
  ]);

  await expect
    .poll(() => savedQuestions)
    .toEqual(["What is the tech stack?", "What is the tech stack?"]);
});

test("a claim opens the code it cites, with real file line numbers", async ({ page }) => {
  const chunkRequests: string[] = [];
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
      if (path.includes("/repos/repo-123/ask") && method === "POST") {
        const answer = answerFor("a first-time outside contributor preparing a pull request");
        if (path.endsWith("/stream")) {
          return route.fulfill({
            status: 200,
            contentType: "text/event-stream",
            headers: sseHeaders,
            body: askStreamBody(answer),
          });
        }
        return route.fulfill({ status: 200, contentType: "application/json", body: answer });
      }
      if (path.includes("/chunks/")) {
        chunkRequests.push(path);
        // Deliberately a different span from the claim's ref (1-20).
        //
        // Production cannot produce this: `read_chunks` matches on exact
        // (file_path, start_line, end_line), so a resolved chunk always
        // carries the span that was asked for. That equality is exactly why
        // the mock has to disagree — with consistent numbers, a gutter reading
        // the claim's ref and one reading the chunk's ref are
        // indistinguishable, and the assertion would prove nothing.
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            chunk_id: "chunk-123",
            repo_id: "repo-123",
            ref: { file_path: "src/flask/app.py", start_line: 11, end_line: 13, symbol: "Flask" },
            content: "class Flask:\n\n    pass\n",
            summary: null,
          }),
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

  await page.goto("/");
  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Open-source contributor" }).click();
  await page.getByRole("button", { name: "Analyze and ask" }).click();
  await expect(page.getByLabel("Ask this repository")).toBeVisible({
    timeout: 15_000,
  });
  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  const claim = page.getByRole("button", { name: /The Flask class is the main app entry/ });
  await page.locator("summary.claim-group-label").first().click({ timeout: 15_000 });
  await expect(claim).toBeVisible({ timeout: 15_000 });

  // Collapsed until asked for: a claim nobody opens costs no chunk fetch.
  await expect(page.getByText("class Flask:")).toBeHidden();
  expect(chunkRequests).toEqual([]);

  await claim.click();

  // The code the claim cites, which is the whole point of claim-to-code.
  await expect(page.getByText("class Flask:")).toBeVisible({ timeout: 15_000 });
  expect(chunkRequests).toHaveLength(1);

  // Numbered from the chunk's real start line, not from 1, and the blank line
  // in the middle still gets a row so the gutter stays aligned.
  const numbers = await page.locator(".source-line-number").allTextContents();
  expect(numbers).toEqual(["11", "12", "13"]);

  // Clicking again closes it rather than re-fetching.
  await claim.click();
  await expect(page.getByText("class Flask:")).toBeHidden();
  expect(chunkRequests).toHaveLength(1);
});

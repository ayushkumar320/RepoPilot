import { expect, test } from "@playwright/test";

import { askStreamBody, sseHeaders } from "./sse";

const repoUrl = process.env.PLAYWRIGHT_REPO_URL ?? "https://github.com/pallets/flask";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

/**
 * Captured verbatim from the live endpoint against an indexed flask snapshot,
 * not written from the TypeScript type. A mock invented from the type is
 * exactly what hides a shape mismatch — this project has been bitten by that
 * before, when a Playwright mock masked the tour SSE event-shape bug.
 *
 * Trimmed to four neighbours that cover every branch the UI has: resolved and
 * clickable, internal but unresolved, and external.
 */
const neighboursResponse = JSON.stringify({
  symbol: "Flask",
  available: true,
  found: true,
  total: 11,
  truncated: true,
  neighbours: [
    {
      symbol: "flask.sessions.SecureCookieSessionInterface",
      label: "SecureCookieSessionInterface",
      edge: "calls",
      kind: "class",
      external: false,
      resolved: true,
      chunk_id: "chunk-neighbour-1",
      ref: {
        file_path: "src/flask/sessions.py",
        start_line: 284,
        end_line: 385,
        symbol: "flask.sessions.SecureCookieSessionInterface",
      },
    },
    {
      symbol: "flask.sansio.app.App",
      label: "App",
      edge: "inherits",
      kind: "class",
      external: false,
      resolved: true,
      chunk_id: "chunk-neighbour-2",
      ref: {
        file_path: "src/flask/sansio/app.py",
        start_line: 59,
        end_line: 1013,
        symbol: "flask.sansio.app.App",
      },
    },
    {
      symbol: "flask.globals.FlaskProxy",
      label: "FlaskProxy",
      edge: "inherited_by",
      kind: null,
      external: false,
      resolved: false,
      chunk_id: null,
      ref: null,
    },
    {
      symbol: "datetime.timedelta",
      label: "timedelta",
      edge: "calls",
      kind: null,
      external: true,
      resolved: false,
      chunk_id: null,
      ref: null,
    },
  ],
});

const answer = JSON.stringify({
  answer: "Flask is the application object.",
  claims: [
    {
      id: "claim-1",
      text: "The Flask class is the main app entry.",
      refs: [{ file_path: "src/flask/app.py", start_line: 1, end_line: 20, symbol: "Flask" }],
      status: "verified",
      verifier_note: "Grounded against app.py.",
      retrieval_path: ["vector_search:k=8"],
    },
  ],
  retrieval_path: ["vector_search:k=8"],
});

async function mockApi(
  page: import("@playwright/test").Page,
  graphBody: string | ((symbol: string) => string),
  answerBody: string = answer,
) {
  await page.route(
    new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    async (route) => {
      const url = new URL(route.request().url());
      const path = url.pathname;
      const method = route.request().method();

      if (path.includes("/graph/neighbours")) {
        // Keyed by symbol, so a test can prove *which* claim the panel asked about.
        const body =
          typeof graphBody === "string"
            ? graphBody
            : graphBody(url.searchParams.get("symbol") ?? "");
        return route.fulfill({ status: 200, contentType: "application/json", body });
      }
      if (path.includes("/chunks/")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            chunk_id: "chunk-neighbour-1",
            repo_id: "repo-123",
            ref: {
              file_path: "src/flask/sessions.py",
              start_line: 284,
              end_line: 385,
              symbol: "flask.sessions.SecureCookieSessionInterface",
            },
            content: "class SecureCookieSessionInterface(SessionInterface):\n    pass",
            summary: null,
          }),
        });
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
      if (path.endsWith("/repos/repo-123/ask/stream") && method === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          headers: sseHeaders,
          body: askStreamBody(answerBody),
        });
      }
      if (path.endsWith("/repos/repo-123/ask") && method === "POST") {
        return route.fulfill({ status: 200, contentType: "application/json", body: answerBody });
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
      if (path.endsWith("/tours") && method === "POST") {
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ tour_id: "tour-123" }),
        });
      }
      return route.fulfill({ status: 200, contentType: "application/json", body: "{}" });
    },
  );
}

async function askAQuestion(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("Public GitHub URL").fill(repoUrl);
  await page.getByRole("button", { name: "Open-source contributor" }).click();
  await page.getByRole("button", { name: "Analyze and ask" }).click();
  await expect(page.getByLabel("Ask this repository")).toBeVisible({
    timeout: 15_000,
  });
  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByText("Flask is the application object.")).toBeVisible({
    timeout: 15_000,
  });
  // Sources now fold into a "Verified sources" disclosure, so everything a
  // claim carries — its citation, the Related code panel — is inside it.
  await openSources(page);
}

/** Unfold the per-answer sources list. */
async function openSources(page: import("@playwright/test").Page) {
  await page.locator("summary.claim-group-label").first().click();
}

test("related code expands a claim into its graph neighbours", async ({ page }) => {
  await mockApi(page, neighboursResponse);
  await askAQuestion(page);

  // Collapsed by default: the panel must not cost a request nobody asked for.
  await expect(page.getByText("SecureCookieSessionInterface")).toBeHidden();

  await page.getByRole("button", { name: "Related code" }).click();

  // Grouped by edge kind, in reading order.
  await expect(page.getByText("Calls", { exact: true })).toBeVisible();
  await expect(page.getByText("Inherits", { exact: true })).toBeVisible();

  // A resolved neighbour shows its real file:line.
  await expect(page.getByText("src/flask/sansio/app.py:59-1013")).toBeVisible();

  // An unresolved one is present but explains itself instead of offering a
  // dead link — and is never given an invented file:line.
  await expect(page.getByText("no indexed source")).toBeVisible();
  await expect(page.getByText("outside this repository")).toBeVisible();

  // Truncation is stated rather than silently hiding the rest.
  await expect(page.getByText("Showing 4 of 11.")).toBeVisible();
});

test("a neighbour expands to its source", async ({ page }) => {
  await mockApi(page, neighboursResponse);
  await askAQuestion(page);

  await page.getByRole("button", { name: "Related code" }).click();
  await page.getByRole("button", { name: /SecureCookieSessionInterface/ }).click();

  await expect(page.getByText("class SecureCookieSessionInterface(SessionInterface):")).toBeVisible(
    { timeout: 10_000 },
  );
});

test("a repo with no python graph says so rather than showing an empty list", async ({ page }) => {
  await mockApi(
    page,
    JSON.stringify({
      symbol: "Flask",
      available: false,
      found: false,
      neighbours: [],
      total: 0,
      truncated: false,
    }),
  );
  await askAQuestion(page);

  await page.getByRole("button", { name: "Related code" }).click();
  await expect(page.getByText(/Dependency graphs are built from Python source/)).toBeVisible();
});

/** Two claims on one answer, each naming a different symbol. */
const twoClaimAnswer = JSON.stringify({
  answer: "Flask is the application object.",
  claims: [
    {
      id: "claim-1",
      text: "The Flask class is the main app entry.",
      refs: [{ file_path: "src/flask/app.py", start_line: 1, end_line: 20, symbol: "Flask" }],
      status: "verified",
      verifier_note: null,
      retrieval_path: ["vector_search:k=8"],
    },
    {
      id: "claim-2",
      text: "Sessions are handled by the session interface.",
      refs: [
        {
          file_path: "src/flask/sessions.py",
          start_line: 100,
          end_line: 160,
          symbol: "flask.sessions.SessionInterface",
        },
      ],
      status: "verified",
      verifier_note: null,
      retrieval_path: ["vector_search:k=8"],
    },
  ],
  retrieval_path: ["vector_search:k=8"],
});

function neighbourNamed(label: string): string {
  return JSON.stringify({
    symbol: "whatever",
    available: true,
    found: true,
    total: 1,
    truncated: false,
    neighbours: [
      {
        symbol: `flask.${label}`,
        label,
        edge: "calls",
        kind: "function",
        external: false,
        resolved: true,
        chunk_id: "chunk-neighbour-1",
        ref: {
          file_path: "src/flask/x.py",
          start_line: 1,
          end_line: 2,
          symbol: `flask.${label}`,
        },
      },
    ],
  });
}

test("the panel follows the selected claim rather than always the first", async ({ page }) => {
  const asked: string[] = [];
  await mockApi(
    page,
    (symbol) => {
      asked.push(symbol);
      return neighbourNamed(symbol === "Flask" ? "AppNeighbour" : "SessionNeighbour");
    },
    twoClaimAnswer,
  );
  await askAQuestion(page);

  // Untouched, the panel anchors on the first claim that names a symbol.
  await page.getByRole("button", { name: "Related code" }).click();
  await expect(page.getByText("AppNeighbour")).toBeVisible({ timeout: 10_000 });

  // Selecting the second claim re-anchors it. Before this was wired, clicking
  // a claim only restyled the row and the panel kept showing the first one's.
  await page.getByRole("button", { name: /Sessions are handled/ }).click();
  await page.getByRole("button", { name: "Related code" }).click();
  await expect(page.getByText("SessionNeighbour")).toBeVisible({ timeout: 10_000 });

  expect(asked).toEqual(["Flask", "flask.sessions.SessionInterface"]);
});

test("a neighbour opens its own neighbours, and the walk stops at a stated depth", async ({
  page,
}) => {
  // Each symbol's only neighbour is the next link, so the chain is unambiguous.
  const chain: Record<string, string> = {
    Flask: "one",
    "flask.one": "two",
    "flask.two": "three",
  };
  const asked: string[] = [];
  await mockApi(page, (symbol) => {
    asked.push(symbol);
    return neighbourNamed(chain[symbol] ?? "end");
  });
  await askAQuestion(page);

  // Depth 0 — the claim's own panel.
  await page.getByRole("button", { name: "Related code" }).click();
  await expect(page.getByText("one")).toBeVisible({ timeout: 10_000 });

  // Each hop: open the neighbour, then open the panel that appears under it.
  // The nested toggle is named for the symbol, so "who calls the thing that
  // calls this" stays legible rather than three identical "Related code" rows.
  for (const [row, next] of [
    ["one", "two"],
    ["two", "three"],
  ] as const) {
    await page.getByRole("button", { name: new RegExp(row) }).first().click();
    const nested = page.getByRole("button", { name: `Related to ${row}` });
    await expect(nested).toBeVisible({ timeout: 10_000 });
    await nested.click();
    await expect(page.getByText(next)).toBeVisible({ timeout: 10_000 });
  }

  // MAX_DEPTH reached. The panel says so rather than offering a control that
  // would keep nesting forever — cycles are normal in a call graph.
  await page.getByRole("button", { name: /three/ }).first().click();
  await expect(page.getByText("Deepest step shown.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("button", { name: "Related to three" })).toHaveCount(0);

  // One request per step the reader actually took — no prefetched tree.
  expect(asked).toEqual(["Flask", "flask.one", "flask.two"]);
});

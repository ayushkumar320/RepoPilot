import { expect, test } from "@playwright/test";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

const sseHeaders = { "Cache-Control": "no-cache", Connection: "keep-alive" };

/** Two claims pointing at different files, so selecting the second is a real
 *  change of source rather than a re-select of the one already shown. */
const CLAIMS = [
  { id: "claim-app", file: "src/flask/app.py", start: 1, end: 4, symbol: "Flask" },
  { id: "claim-blueprints", file: "src/flask/blueprints.py", start: 10, end: 13, symbol: "Blueprint" },
];

function bodyFor(file: string): string {
  return `# ${file}\nclass Thing:\n    pass\n# end`;
}

const answer = JSON.stringify({
  answer: "Two sources back this answer.",
  claims: CLAIMS.map((c) => ({
    id: c.id,
    text: `Claim about ${c.file}`,
    refs: [{ file_path: c.file, start_line: c.start, end_line: c.end, symbol: c.symbol }],
    status: "verified",
    verifier_note: "Grounded.",
    retrieval_path: ["vector_search:k=8"],
  })),
  retrieval_path: ["vector_search:k=8"],
});

test.beforeEach(async ({ page }) => {
  await page.route(
    new RegExp(apiBaseUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")),
    async (route) => {
      const path = new URL(route.request().url()).pathname;
      const method = route.request().method();
      const json = (body: string, status = 200) =>
        route.fulfill({ status, contentType: "application/json", body });

      if (path.endsWith("/account/usage")) {
        return json(
          JSON.stringify({
            free_repositories_remaining: 1,
            provider_connected: false,
            groq_connected: false,
            huggingface_connected: false,
            credential_storage: "session_only",
          }),
        );
      }
      if (path.endsWith("/repos") && method === "POST") {
        return json(JSON.stringify({ repo_id: "repo-123", status: "queued" }), 202);
      }
      if (path.includes("/repos/repo-123/status")) {
        return json(JSON.stringify({ status: "ready", progress: 100 }));
      }
      if (path.includes("/repos/repo-123/first-impression")) {
        return route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          headers: sseHeaders,
          body: 'event: done\ndata: {"v":1}\n\n',
        });
      }
      if (path.includes("/repos/repo-123/ask") && method === "POST") return json(answer);
      if (path.endsWith("/me")) {
        return json(JSON.stringify({ session_id: "anon", authenticated: false }));
      }
      if (path.endsWith("/tours") && method === "GET") return json("[]");
      if (path.endsWith("/tours") && method === "POST") {
        return json(JSON.stringify({ tour_id: "tour-123" }), 201);
      }
      if (path.includes("/tours/tour-123/messages")) return json(JSON.stringify({ ordinal: 0 }), 201);

      if (path.includes("/chunks/")) {
        // The id encodes the ref, so decode it and answer with the matching
        // file rather than always returning the same source.
        const encoded = path.split("/chunks/")[1];
        const ref = JSON.parse(Buffer.from(encoded, "base64url").toString("utf-8"));
        return json(
          JSON.stringify({
            chunk_id: encoded,
            repo_id: "repo-123",
            ref: {
              file_path: ref.file_path,
              start_line: ref.start_line,
              end_line: ref.end_line,
              symbol: ref.symbol,
            },
            content: bodyFor(ref.file_path),
            summary: null,
          }),
        );
      }
      return route.fallback();
    },
  );
});

test("selecting a different claim replays the code panel's arrival", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Public GitHub URL").fill("https://github.com/pallets/flask");
  await page.getByRole("button", { name: "Open-source contributor" }).click();
  await page.getByRole("button", { name: "Analyze and ask" }).click();

  await expect(page.getByRole("heading", { name: "Ask this repository" })).toBeVisible({
    timeout: 15_000,
  });
  await page.getByLabel("Ask this repository").fill("What is the tech stack?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  // The newest answer focuses its first source on its own.
  await expect(page.getByText(`# ${CLAIMS[0].file}`)).toBeVisible({ timeout: 15_000 });
  // Let that first arrival finish, so anything still running afterwards
  // belongs to the second selection.
  await page.waitForTimeout(800);

  const replay = await page.evaluate(() => {
    const rows = document.querySelectorAll<HTMLButtonElement>(".claim-row");
    if (rows.length < 2) return { error: `expected 2 claim rows, saw ${rows.length}` };
    const before = document.querySelector(".code-frame pre");
    rows[1].click();
    return new Promise((resolve) => {
      // Poll until the new source has rendered, then read what is animating.
      const started = performance.now();
      const check = () => {
        const now = document.querySelector(".code-frame pre");
        if (now && now !== before) {
          return resolve({
            // Line numbers are their own cells, so read the whole block
            // rather than trying to pick out the first source line.
            body: (now as HTMLElement).innerText,
            codeArriving: now.getAnimations().map((a) => (a as CSSAnimation).animationName ?? ""),
            rangeLanding: [...document.querySelectorAll(".code-line-active")]
              .flatMap((n) => n.getAnimations())
              .map((a) => (a as CSSAnimation).animationName ?? ""),
          });
        }
        if (performance.now() - started > 8000) return resolve({ error: "source never changed" });
        requestAnimationFrame(check);
      };
      check();
    });
  });

  const result = replay as Record<string, unknown>;
  expect(result.error).toBeUndefined();
  expect(result.body, "panel still shows the previous source").toContain(CLAIMS[1].file);
  expect(result.codeArriving, "new source appeared with no arrival").toContain("code-arrive");
  expect(result.rangeLanding, "claimed range did not announce itself").toContain(
    "claimed-range-land",
  );
});

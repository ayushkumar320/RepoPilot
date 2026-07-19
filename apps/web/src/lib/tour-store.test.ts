import assert from "node:assert/strict";
import test from "node:test";

import { applyTourEvent, hydrateViewer, initialTourStoreState, selectClaim } from "./tour-store.ts";

test("claim selection updates viewer state", () => {
  const repoId = "pallets/flask";
  const seeded = applyTourEvent(
    initialTourStoreState,
    {
      event: "section_start",
      v: 1,
      order: 0,
      title: "Entry points",
    },
    repoId,
  );
  const withClaim = applyTourEvent(
    seeded,
    {
      event: "claim",
      v: 1,
      id: "claim-1",
      text: "Start with Flask",
      refs: [
        {
          file_path: "src/flask/app.py",
          start_line: 10,
          end_line: 24,
          symbol: "Flask",
        },
      ],
      status: "verified",
      verifier_note: "Grounded",
      retrieval_path: ["graph_query:hubs"],
    },
    repoId,
  );

  const selected = selectClaim(withClaim, "claim-1");

  assert.equal(selected.selectedClaimId, "claim-1");
  assert.equal(selected.viewer.filePath, "src/flask/app.py");
  assert.equal(selected.viewer.startLine, 10);
});

test("viewer hydration carries chunk content", () => {
  const hydrated = hydrateViewer(initialTourStoreState, {
    chunk_id: "chunk-1",
    repo_id: "pallets/flask@abc",
    ref: {
      file_path: "src/flask/app.py",
      start_line: 10,
      end_line: 24,
      symbol: "Flask",
    },
    content: "class Flask:",
    summary: "Flask application object",
  });

  assert.equal(hydrated.viewer.content, "class Flask:");
  assert.equal(hydrated.viewer.summary, "Flask application object");
});

test("selecting another claim clears stale viewer content", () => {
  const repoId = "pallets/flask";
  let state = applyTourEvent(
    initialTourStoreState,
    { event: "section_start", v: 1, order: 0, title: "Entry points" },
    repoId,
  );
  for (const [id, filePath] of [
    ["claim-1", "src/flask/app.py"],
    ["claim-2", "src/flask/cli.py"],
  ] as const) {
    state = applyTourEvent(
      state,
      {
        event: "claim",
        v: 1,
        id,
        text: `Read ${filePath}`,
        refs: [{ file_path: filePath, start_line: 1, end_line: 10 }],
        status: "verified",
        retrieval_path: ["hybrid_search"],
      },
      repoId,
    );
  }
  state = hydrateViewer(state, {
    chunk_id: state.claimsById["claim-1"].chunkId,
    repo_id: repoId,
    ref: { file_path: "src/flask/app.py", start_line: 1, end_line: 10 },
    content: "class Flask:",
    summary: "Application object",
  });

  const selected = selectClaim(state, "claim-2");

  assert.equal(selected.viewer.filePath, "src/flask/cli.py");
  assert.equal(selected.viewer.content, undefined);
  assert.equal(selected.viewer.summary, undefined);
});

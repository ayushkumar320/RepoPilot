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

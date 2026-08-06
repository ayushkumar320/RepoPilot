import assert from "node:assert/strict";
import { test } from "node:test";

import type { ClaimPayload } from "./api/generated.ts";
import {
  appendExchange,
  applyRepoStatus,
  encodeChunkId,
  hydrateFromTour,
  initialSessionState,
  personaLabel,
  selectClaim,
} from "./session-store.ts";

const REPO_ID = "pallets%2Fflask";

function claim(id: string, line: number): ClaimPayload {
  return {
    id,
    text: `claim ${id}`,
    refs: [{ file_path: "src/flask/app.py", start_line: line, end_line: line + 5, symbol: "Flask" }],
    status: "verified",
    retrieval_path: ["vector_search:k=8"],
  };
}

test("appendExchange records the question, answer, and claims in order", () => {
  const state = appendExchange(initialSessionState, {
    question: "What is the entry point?",
    answer: "The Flask class.",
    claims: [claim("c1", 1), claim("c2", 30)],
    personaLabel: "a maintainer",
    repoId: REPO_ID,
  });

  assert.equal(state.exchanges.length, 1);
  assert.equal(state.exchanges[0].question, "What is the entry point?");
  assert.equal(state.exchanges[0].personaLabel, "a maintainer");
  assert.deepEqual(state.exchanges[0].claimIds, ["c1", "c2"]);
  assert.equal(Object.keys(state.claimsById).length, 2);
});

test("appendExchange focuses the newest answer's first source", () => {
  let state = appendExchange(initialSessionState, {
    question: "q1",
    answer: "a1",
    claims: [claim("c1", 1)],
    personaLabel: "a learner",
    repoId: REPO_ID,
  });
  assert.equal(state.selectedClaimId, "c1");

  state = appendExchange(state, {
    question: "q2",
    answer: "a2",
    claims: [claim("c2", 90)],
    personaLabel: "a learner",
    repoId: REPO_ID,
  });
  // Selection follows the latest evidence, not the first thing ever selected.
  assert.equal(state.selectedClaimId, "c2");
});

test("exchanges accumulate so two personas can be compared side by side", () => {
  let state = appendExchange(initialSessionState, {
    question: "Same question",
    answer: "contributor answer",
    claims: [claim("c1", 1)],
    personaLabel: "a contributor",
    repoId: REPO_ID,
  });
  state = appendExchange(state, {
    question: "Same question",
    answer: "competitor answer",
    claims: [claim("c2", 1)],
    personaLabel: "a competitor",
    repoId: REPO_ID,
  });

  assert.deepEqual(
    state.exchanges.map((exchange) => exchange.personaLabel),
    ["a contributor", "a competitor"],
  );
  assert.equal(state.exchanges[0].answer, "contributor answer");
});

test("appendExchange skips claims with no refs rather than throwing", () => {
  const bare = { ...claim("c1", 1), refs: [] };
  const state = appendExchange(initialSessionState, {
    question: "q",
    answer: "a",
    claims: [bare],
    personaLabel: "anyone",
    repoId: REPO_ID,
  });
  assert.deepEqual(state.exchanges[0].claimIds, []);
  assert.equal(state.selectedClaimId, undefined);
});

test("selectClaim moves the selection to the clicked claim", () => {
  let state = appendExchange(initialSessionState, {
    question: "q",
    answer: "a",
    claims: [claim("c1", 1), claim("c2", 40)],
    personaLabel: "anyone",
    repoId: REPO_ID,
  });
  assert.equal(state.selectedClaimId, "c1");

  state = selectClaim(state, "c2");
  assert.equal(state.selectedClaimId, "c2");
});

test("selectClaim on an unknown id is a no-op", () => {
  const state = selectClaim(initialSessionState, "missing");
  assert.equal(state, initialSessionState);
});

test("encodeChunkId round-trips through base64url", () => {
  const encoded = encodeChunkId(REPO_ID, {
    file_path: "src/flask/app.py",
    start_line: 1,
    end_line: 20,
    symbol: "Flask",
  });
  const decoded = JSON.parse(Buffer.from(encoded, "base64url").toString("utf-8")) as {
    repo_id: string;
    file_path: string;
  };
  assert.equal(decoded.repo_id, REPO_ID);
  assert.equal(decoded.file_path, "src/flask/app.py");
});

test("applyRepoStatus stores the latest indexing status", () => {
  const state = applyRepoStatus(initialSessionState, { status: "ready", progress: 100 });
  assert.equal(state.repoStatus?.status, "ready");
});

test("personaLabel prefers audience framing, falls back to raw text", () => {
  assert.equal(personaLabel({ raw_text: "raw", audience_framing: "a reviewer" }), "a reviewer");
  assert.equal(personaLabel({ raw_text: "raw" }), "raw");
  assert.equal(personaLabel(null), "No lens");
});

test("hydrateFromTour replays persisted exchanges in ask order", () => {
  const state = hydrateFromTour(
    {
      repo_id: REPO_ID,
      messages: [
        {
          ordinal: 0,
          question: "q1",
          answer: "a1",
          claims: [claim("c1", 1)],
          persona_label: "a learner",
        },
        {
          ordinal: 1,
          question: "q2",
          answer: "a2",
          claims: [claim("c2", 30)],
          persona_label: "a maintainer",
        },
      ],
    },
    "Indexed snapshot.",
  );

  assert.equal(state.firstImpression, "Indexed snapshot.");
  assert.deepEqual(
    state.exchanges.map((exchange) => [exchange.question, exchange.personaLabel]),
    [
      ["q1", "a learner"],
      ["q2", "a maintainer"],
    ],
  );
  assert.deepEqual(Object.keys(state.claimsById).sort(), ["c1", "c2"]);
  assert.equal(state.selectedClaimId, "c2");
});

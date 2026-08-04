import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { test } from "node:test";

import { signSession, stableSessionId } from "./identity.ts";

// Golden values produced by the API's own primitives:
//   uuid.uuid5(UUID("6f0d5a5c-1a0f-4a3f-9a3a-0f7d2a6b91c4"), "github:4242")
// If either of these drifts, every signed-in user silently falls back to a
// fresh anonymous session and loses their history.
const SESSION_ID = "72468993-377e-5e43-bb4f-c6a5e7f34126";
const SECRET = "repopilot-development-session-secret";

test("stableSessionId matches Python uuid5 for the same account", async () => {
  assert.equal(await stableSessionId("4242"), SESSION_ID);
});

test("stableSessionId is deterministic and account-specific", async () => {
  assert.equal(await stableSessionId("4242"), await stableSessionId("4242"));
  assert.notEqual(await stableSessionId("4242"), await stableSessionId("4243"));
});

test("signSession matches signed_session() in app.py", async () => {
  const expected = createHmac("sha256", SECRET).update(SESSION_ID).digest("hex");
  assert.equal(await signSession(SESSION_ID, SECRET), `${SESSION_ID}.${expected}`);
});

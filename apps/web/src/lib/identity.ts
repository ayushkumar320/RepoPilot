/**
 * Bridge between the OAuth identity and the API's signed session cookie.
 *
 * The API already trusts one thing: `repopilot_session`, an HMAC-signed
 * `session_id`. Logging a user in therefore means minting a *stable*
 * `session_id` for their GitHub account and signing it with the same secret,
 * so every existing per-session feature becomes per-user with no API change.
 *
 * Web Crypto only — this runs in Next's edge middleware, where `node:crypto`
 * is unavailable.
 */

export const SESSION_COOKIE = "repopilot_session";

/** Fixed namespace for uuidv5; changing it re-keys every logged-in account. */
const NAMESPACE = "6f0d5a5c-1a0f-4a3f-9a3a-0f7d2a6b91c4";

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function uuidBytes(uuid: string): Uint8Array {
  const digits = uuid.replace(/-/g, "");
  const bytes = new Uint8Array(16);
  for (let index = 0; index < 16; index += 1) {
    bytes[index] = Number.parseInt(digits.slice(index * 2, index * 2 + 2), 16);
  }
  return bytes;
}

/**
 * RFC 4122 v5 (SHA-1, name-based) UUID — the same value Python's
 * `uuid.uuid5(NAMESPACE, name)` produces, so ids stay comparable across the
 * stack. Deterministic: same GitHub account, same session id, every device.
 */
export async function stableSessionId(providerAccountId: string): Promise<string> {
  const name = new TextEncoder().encode(`github:${providerAccountId}`);
  const input = new Uint8Array(16 + name.length);
  input.set(uuidBytes(NAMESPACE), 0);
  input.set(name, 16);

  const digest = new Uint8Array(await crypto.subtle.digest("SHA-1", input));
  const bytes = digest.slice(0, 16);
  bytes[6] = (bytes[6] & 0x0f) | 0x50; // version 5
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // RFC 4122 variant

  const value = hex(bytes);
  return [
    value.slice(0, 8),
    value.slice(8, 12),
    value.slice(12, 16),
    value.slice(16, 20),
    value.slice(20),
  ].join("-");
}

/**
 * `${session_id}.${hmac_sha256_hex}` — byte-for-byte what
 * `signed_session()` in `apps/api/src/repopilot_api/app.py` produces. The two
 * sides must share REPOPILOT_SESSION_SECRET or the API silently discards the
 * cookie and mints a fresh anonymous session.
 */
export async function signSession(sessionId: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(sessionId));
  return `${sessionId}.${hex(new Uint8Array(signature))}`;
}

export function sessionSecret(): string {
  return process.env.REPOPILOT_SESSION_SECRET ?? "repopilot-development-session-secret";
}

export function sessionCookieSecure(): boolean {
  return process.env.REPOPILOT_SESSION_COOKIE_SECURE === "true";
}

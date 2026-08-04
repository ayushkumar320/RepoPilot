import { NextResponse } from "next/server";

import { auth } from "@/auth";
import {
  SESSION_COOKIE,
  sessionCookieSecure,
  sessionSecret,
  signSession,
} from "@/lib/identity";

/**
 * Keeps the API's signed session cookie in step with who is signed in.
 *
 * Signed in  -> cookie holds the stable, GitHub-derived session id.
 * Signing out -> cookie is cleared, so the API mints a fresh anonymous one.
 * Anonymous  -> untouched; the API owns that cookie exactly as before.
 */
const bridge = auth(async (request) => {
  const response = NextResponse.next();
  const secure = sessionCookieSecure();

  if (request.nextUrl.pathname === "/api/auth/signout") {
    response.cookies.delete(SESSION_COOKIE);
    return response;
  }

  const sessionId = request.auth?.sessionId;
  if (!sessionId) return response;

  const signed = await signSession(sessionId, sessionSecret());
  if (request.cookies.get(SESSION_COOKIE)?.value === signed) return response;

  response.cookies.set(SESSION_COOKIE, signed, {
    httpOnly: true,
    secure,
    sameSite: secure ? "none" : "lax",
    maxAge: 60 * 60 * 24 * 30,
    path: "/",
  });
  return response;
});

/**
 * With no GitHub OAuth app configured there is nothing to bridge, and calling
 * into NextAuth without AUTH_SECRET would fail every request — so a stock
 * local checkout skips the wrapper entirely.
 */
const middleware: typeof bridge = (...args) => {
  if (!process.env.AUTH_GITHUB_ID) return NextResponse.next();
  return bridge(...args);
};

export default middleware;

export const config = {
  // Skip static assets; everything a user or the API client touches runs through.
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

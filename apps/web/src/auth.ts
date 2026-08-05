import NextAuth, { type NextAuthConfig } from "next-auth";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";

import { stableSessionId } from "@/lib/identity";

/**
 * Google and GitHub, JWT sessions, no database adapter.
 *
 * Our own `product_accounts` row (keyed by `sessionId` below) is the user
 * record, so NextAuth's four adapter tables would be dead weight. Each
 * provider is wired only when its credentials exist, so a checkout with only
 * one of the two still boots.
 */
const providers: NextAuthConfig["providers"] = [];
if (process.env.AUTH_GOOGLE_ID) providers.push(Google);
if (process.env.AUTH_GITHUB_ID) providers.push(GitHub);

/** Provider ids to offer on the sign-in gate, in display order. */
export const enabledProviders = providers.length
  ? ([
      ...(process.env.AUTH_GOOGLE_ID ? ["google"] : []),
      ...(process.env.AUTH_GITHUB_ID ? ["github"] : []),
    ] as const)
  : ([] as const);

/** With no OAuth app configured there is no gate — the app stays anonymous. */
export const authEnabled = providers.length > 0;

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  session: { strategy: "jwt" },
  // RepoPilot is self-hosted, so Auth.js will not infer the request host on
  // its own — without this every callback fails as `UntrustedHost`, which the
  // browser only ever sees as the generic `error=Configuration` page.
  trustHost: true,
  // Dev-only: turns that generic page into a named cause in the server log.
  debug: process.env.NODE_ENV !== "production",
  callbacks: {
    async jwt({ token, account }) {
      if (account?.providerAccountId) {
        token.providerAccountId = account.providerAccountId;
        token.provider = account.provider;
        token.sessionId = await stableSessionId(account.providerAccountId, account.provider);
      }
      return token;
    },
    session({ session, token }) {
      session.sessionId = typeof token.sessionId === "string" ? token.sessionId : undefined;
      session.providerAccountId =
        typeof token.providerAccountId === "string" ? token.providerAccountId : undefined;
      session.provider = typeof token.provider === "string" ? token.provider : undefined;
      return session;
    },
  },
});

import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

import { stableSessionId } from "@/lib/identity";

/**
 * GitHub only, JWT sessions, no database adapter.
 *
 * The product's input is a GitHub URL, so the user already has the account;
 * and our own `product_accounts` row (keyed by `sessionId` below) is the user
 * record, so NextAuth's four adapter tables would be dead weight.
 */
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [GitHub],
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
        token.sessionId = await stableSessionId(account.providerAccountId);
      }
      return token;
    },
    session({ session, token }) {
      session.sessionId = typeof token.sessionId === "string" ? token.sessionId : undefined;
      session.providerAccountId =
        typeof token.providerAccountId === "string" ? token.providerAccountId : undefined;
      return session;
    },
  },
});

import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    /** Stable, GitHub-derived id shared with the API via the signed cookie. */
    sessionId?: string;
    providerAccountId?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    sessionId?: string;
    providerAccountId?: string;
  }
}

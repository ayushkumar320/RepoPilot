import { auth, signIn, signOut } from "@/auth";
import RepoPilotApp from "@/components/repopilot-app";

export default async function Home() {
  // Auth is optional: with no GitHub OAuth app configured the page still
  // renders the anonymous product exactly as before.
  const session = process.env.AUTH_GITHUB_ID ? await auth() : null;

  return (
    <RepoPilotApp
      viewer={
        session?.user && session.providerAccountId
          ? {
              providerAccountId: session.providerAccountId,
              name: session.user.name ?? null,
              email: session.user.email ?? null,
              image: session.user.image ?? null,
            }
          : null
      }
      authEnabled={Boolean(process.env.AUTH_GITHUB_ID)}
      signInAction={async () => {
        "use server";
        await signIn("github");
      }}
      signOutAction={async () => {
        "use server";
        await signOut();
      }}
    />
  );
}

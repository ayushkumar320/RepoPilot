import { auth, authEnabled, enabledProviders, signIn, signOut } from "@/auth";
import RepoPilotApp from "@/components/repopilot-app";

const PROVIDER_LABELS: Record<string, string> = {
  google: "Continue with Google",
  github: "Continue with GitHub",
};

export default async function Home() {
  // Auth is optional: with no OAuth app configured the page still renders the
  // anonymous product exactly as before.
  const session = authEnabled ? await auth() : null;
  const viewer =
    session?.user && session.providerAccountId
      ? {
          provider: session.provider ?? "github",
          providerAccountId: session.providerAccountId,
          name: session.user.name ?? null,
          email: session.user.email ?? null,
          image: session.user.image ?? null,
        }
      : null;

  // Signed-out visitors get the gate, not the product: a tour is tied to an
  // account, so the account comes first and the repo question comes second.
  if (authEnabled && !viewer) {
    return (
      <main className="app-shell">
        <section className="signin-gate">
          <p className="section-kicker">Sign in</p>
          <h1>Ask a codebase anything, as anyone.</h1>
          <p className="intro-copy">
            Sign in first so your tours, lenses, and answers stay with your account. Next you pick
            the repository and the lens you are reading through.
          </p>
          <div className="signin-actions">
            {enabledProviders.map((provider) => (
              <form
                key={provider}
                action={async () => {
                  "use server";
                  await signIn(provider);
                }}
              >
                <button className="button button-primary" type="submit">
                  {PROVIDER_LABELS[provider] ?? `Continue with ${provider}`}
                </button>
              </form>
            ))}
          </div>
        </section>
      </main>
    );
  }

  return (
    <RepoPilotApp
      viewer={viewer}
      signOutAction={async () => {
        "use server";
        await signOut();
      }}
    />
  );
}

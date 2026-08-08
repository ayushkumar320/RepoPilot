"use client";

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  ClockCountdown,
  Eye,
  EyeSlash,
  FileCode,
  GitBranch,
  GithubLogo,
  LockKey,
  MagnifyingGlass,
  PaperPlaneTilt,
  ShieldCheck,
  SignOut,
  Trash,
  UserFocus,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import { type FormEvent, useEffect, useMemo, useReducer, useRef, useState } from "react";

import { GraphNeighbours } from "./graph-neighbours";
import {
  ApiError,
  api,
  type AccountUsage,
  type ClaimStatus,
  type IntentProfile,
  type RepoEvent,
  type RepoStatus,
  type TourSummary,
} from "@/lib/api/generated";
import {
  CUSTOM_PERSONA_ID,
  PERSONAS,
  fallbackCustomProfile,
  personaById,
} from "@/lib/personas";
import {
  appendExchange,
  applyFirstImpression,
  applyRepoStatus,
  hydrateFromTour,
  initialSessionState,
  personaLabel,
  selectClaim,
  type SessionState,
} from "@/lib/session-store";

function claimBadgeClass(status: ClaimStatus): string {
  if (status === "flagged" || status === "rejected") {
    return "status-badge status-badge-warning";
  }
  // "unverified" = the verifier could not run (e.g. every provider was
  // exhausted). Neutral treatment — neither confirmed nor found wanting.
  if (status === "unverified") {
    return "status-badge status-badge-neutral";
  }
  return "status-badge status-badge-success";
}

function claimBadgeLabel(status: ClaimStatus): string {
  if (status === "flagged" || status === "rejected") return "Review";
  if (status === "unverified") return "Unverified";
  return "Verified";
}

function statusLabel(status?: RepoStatus): string {
  if (!status) return "Not started";
  if (status === "queued") return "Queued";
  if (status === "indexing") return "Indexing repository";
  if (status === "ready") return "Snapshot ready";
  if (status === "stale") return "Cached snapshot ready";
  return "Indexing failed";
}

function repositoryName(repoUrl: string): string {
  try {
    const url = new URL(repoUrl);
    return url.pathname.replace(/^\//, "").replace(/\.git\/?$/, "") || "Repository";
  } catch {
    return "Repository";
  }
}

function validPublicGithubUrl(repoUrl: string): boolean {
  try {
    const url = new URL(repoUrl);
    return (
      url.protocol === "https:" &&
      url.hostname === "github.com" &&
      url.pathname.split("/").filter(Boolean).length === 2
    );
  } catch {
    return false;
  }
}

interface ProviderDialogProps {
  error: string | null;
  onClose: () => void;
  onConnect: (groqKey: string, huggingfaceKey: string) => Promise<void>;
  onDisconnect: () => Promise<void>;
  open: boolean;
  saving: boolean;
  usage: AccountUsage | null;
}

function ProviderDialog({
  error,
  onClose,
  onConnect,
  onDisconnect,
  open,
  saving,
  usage,
}: ProviderDialogProps) {
  const [groqKey, setGroqKey] = useState("");
  const [huggingfaceKey, setHuggingfaceKey] = useState("");
  const [showGroq, setShowGroq] = useState(false);
  const [showHuggingface, setShowHuggingface] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (!open) {
      setGroqKey("");
      setHuggingfaceKey("");
      setShowGroq(false);
      setShowHuggingface(false);
    }
  }, [open]);

  // showModal() is what buys the focus trap, the Escape key, the inert
  // background and the top layer — none of which are worth hand-rolling.
  useEffect(() => {
    const node = dialogRef.current;
    if (!node) return;
    if (open && !node.open) node.showModal();
    if (!open && node.open) node.close();
  }, [open]);

  return (
    <dialog
      className="provider-dialog"
      ref={dialogRef}
      aria-labelledby="provider-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        // A click that lands on the dialog element itself is a backdrop click:
        // the content sits in a child that stops it getting this far.
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <div className="provider-dialog-content">
        <div className="dialog-heading">
          <div className="dialog-icon" aria-hidden="true">
            <LockKey size={21} weight="fill" />
          </div>
          <div>
            <h2 id="provider-dialog-title">
              {usage?.provider_connected ? "Provider connected" : "Continue with your Groq limit"}
            </h2>
            <p>
              Keys go directly to the API and stay with your account, encrypted at rest, so they
              survive signing out. They are never stored in the browser. Disconnect deletes them.
            </p>
          </div>
          <button
            className="icon-button dialog-close"
            type="button"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {usage?.provider_connected ? (
          <div className="connected-provider">
            <div>
              <strong>Groq</strong>
              <span>Connected for repository analysis and questions</span>
            </div>
            <div>
              <strong>Hugging Face</strong>
              <span>{usage.huggingface_connected ? "Connected as fallback" : "Not connected"}</span>
            </div>
            <button
              className="button button-secondary"
              type="button"
              disabled={saving}
              onClick={() => void onDisconnect()}
            >
              {saving ? "Disconnecting" : "Disconnect keys"}
            </button>
          </div>
        ) : (
          <form
            className="provider-form"
            onSubmit={(event) => {
              event.preventDefault();
              void onConnect(groqKey, huggingfaceKey);
            }}
          >
            <div className="credential-field">
              <label htmlFor="groq-api-key">Groq API key</label>
              <div className="secret-input-wrap">
                <input
                  id="groq-api-key"
                  className="text-input"
                  type={showGroq ? "text" : "password"}
                  value={groqKey}
                  onChange={(event) => setGroqKey(event.target.value)}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="gsk_..."
                  aria-describedby="groq-key-help"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowGroq((value) => !value)}
                  aria-label={showGroq ? "Hide Groq key" : "Show Groq key"}
                >
                  {showGroq ? <EyeSlash size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p id="groq-key-help">Required. Usage is charged against your Groq account limits.</p>
            </div>

            <div className="credential-field">
              <label htmlFor="huggingface-api-key">
                Hugging Face token <span>Optional</span>
              </label>
              <div className="secret-input-wrap">
                <input
                  id="huggingface-api-key"
                  className="text-input"
                  type={showHuggingface ? "text" : "password"}
                  value={huggingfaceKey}
                  onChange={(event) => setHuggingfaceKey(event.target.value)}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="hf_..."
                  aria-describedby="hf-key-help"
                />
                <button
                  type="button"
                  onClick={() => setShowHuggingface((value) => !value)}
                  aria-label={
                    showHuggingface ? "Hide Hugging Face token" : "Show Hugging Face token"
                  }
                >
                  {showHuggingface ? <EyeSlash size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p id="hf-key-help">Used only as a fallback when the Groq request cannot complete.</p>
            </div>

            {error ? (
              <div className="dialog-error" role="alert">
                {error}
              </div>
            ) : null}

            <div className="dialog-actions">
              <button className="button button-secondary" type="button" onClick={onClose}>
                Not now
              </button>
              <button
                className="button button-primary"
                type="submit"
                disabled={saving || groqKey.trim().length < 12}
              >
                {saving ? "Connecting" : "Connect keys"}
              </button>
            </div>
          </form>
        )}
      </div>
    </dialog>
  );
}

export interface Viewer {
  provider: string;
  providerAccountId: string;
  name: string | null;
  email: string | null;
  image: string | null;
}

/** Render the answer body: "## " lines become headings, "[3]" citation
 *  markers become superscripts, everything else is a paragraph. The claim
 *  list below the answer carries the actual source links. */
function AnswerBody({ text }: { text: string }) {
  const lines = text.split("\n").filter((line) => line.trim().length > 0);
  return (
    <div className="section-body answer-body">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("#")) {
          return (
            <h3 className="answer-heading" key={index}>
              {trimmed.replace(/^#+\s*/, "")}
            </h3>
          );
        }
        const body = trimmed.replace(/^[-•*]\s*/, "");
        const parts = body.split(/(\[\d+\])/g).filter(Boolean);
        return (
          <p className="answer-line" key={index}>
            {parts.map((part, partIndex) =>
              /^\[\d+\]$/.test(part) ? (
                <sup className="answer-citation" key={partIndex}>
                  {part.slice(1, -1)}
                </sup>
              ) : (
                <span key={partIndex}>{part}</span>
              ),
            )}
          </p>
        );
      })}
    </div>
  );
}

export interface RepoPilotAppProps {
  signOutAction?: () => Promise<void>;
  viewer?: Viewer | null;
}

export default function RepoPilotApp({
  signOutAction,
  viewer = null,
}: RepoPilotAppProps = {}) {
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/flask");
  const [repoId, setRepoId] = useState<string>();
  const [personaId, setPersonaId] = useState<string>(PERSONAS[0].id);
  const [customText, setCustomText] = useState("");
  const [customProfile, setCustomProfile] = useState<IntentProfile | null>(null);
  const [draftingIntent, setDraftingIntent] = useState(false);
  const [askPrompt, setAskPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [asking, setAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [usage, setUsage] = useState<AccountUsage | null>(null);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [providerSaving, setProviderSaving] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [store, setStore] = useState<SessionState>(initialSessionState);
  const [tours, setTours] = useState<TourSummary[]>([]);
  const [tourId, setTourId] = useState<string>();
  const [pollTick, forcePoll] = useReducer((value: number) => value + 1, 0);

  const isCustom = personaId === CUSTOM_PERSONA_ID;
  const profile: IntentProfile | null = useMemo(() => {
    if (isCustom) {
      if (customProfile) return customProfile;
      return customText.trim() ? fallbackCustomProfile(customText) : null;
    }
    return personaById(personaId)?.profile ?? null;
  }, [customProfile, customText, isCustom, personaId]);

  const repoReady = store.repoStatus?.status === "ready" || store.repoStatus?.status === "stale";
  const repoError = store.repoStatus?.status === "error";
  const progress = store.repoStatus?.progress ?? (repoId ? 5 : 0);
  const repoDisplayName = repositoryName(repoUrl);
  // The workspace opens as soon as a snapshot exists — there is no separate
  // "start" step to cross.
  const inWorkspace = Boolean(repoId) && repoReady;

  useEffect(() => {
    void api
      .getAccountUsage()
      .then(setUsage)
      .catch(() => {
        setErrorMessage("Could not load your account usage.");
      });
  }, []);

  // Label the session with who owns it, then load their history. Anonymous
  // visitors skip the label but still get their own (cookie-scoped) tours.
  useEffect(() => {
    let active = true;
    const load = async () => {
      if (viewer) {
        await api
          .saveIdentity({
            provider: viewer.provider,
            provider_account_id: viewer.providerAccountId,
            display_name: viewer.name,
            email: viewer.email,
            avatar_url: viewer.image,
          })
          .catch(() => undefined);
      }
      const listed = await api.listTours().catch(() => [] as TourSummary[]);
      if (active) setTours(listed);
    };
    void load();
    return () => {
      active = false;
    };
  }, [viewer]);

  // Deep link: ?repo=<id>&persona=<id> reopens a repo with the same lens.
  useEffect(() => {
    if (repoId) return;
    const params = new URLSearchParams(window.location.search);
    const routeRepoId = params.get("repo");
    if (!routeRepoId) return;
    const routePersona = params.get("persona");
    if (routePersona && personaById(routePersona)) setPersonaId(routePersona);
    setRepoId(routeRepoId);
    setRepoUrl(`https://github.com/${decodeURIComponent(routeRepoId)}`);
  }, [repoId]);

  useEffect(() => {
    if (!repoId) return;
    const eventSource = new EventSource(api.firstImpressionUrl(repoId), { withCredentials: true });
    const onMessage = (event: MessageEvent<string>) => {
      const parsed = JSON.parse(event.data) as RepoEvent;
      if (parsed.event === "first_impression") {
        setStore((current) => applyFirstImpression(current, parsed));
      }
    };
    eventSource.addEventListener("first_impression", onMessage as EventListener);
    eventSource.addEventListener("done", () => eventSource.close());
    eventSource.addEventListener("error", () => eventSource.close());
    return () => eventSource.close();
  }, [repoId]);

  useEffect(() => {
    if (!repoId || repoReady || repoError) return;
    const timeout = window.setTimeout(async () => {
      try {
        const status = await api.getRepoStatus(repoId);
        setStore((current) => applyRepoStatus(current, status));
        forcePoll();
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : "Could not refresh indexing status.",
        );
      }
    }, 1500);
    return () => window.clearTimeout(timeout);
  }, [repoError, repoId, repoReady, pollTick]);

  // Structure free-text personas server-side once the user stops typing. A
  // failure is not fatal: `profile` already falls back to raw text.
  const structureCustomPersona = async () => {
    const text = customText.trim();
    if (!isCustom || text.length < 8) return;
    setDraftingIntent(true);
    try {
      setCustomProfile(await api.draftIntent(text));
    } catch {
      setCustomProfile(fallbackCustomProfile(text));
    } finally {
      setDraftingIntent(false);
    }
  };

  const submitRepo = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!validPublicGithubUrl(repoUrl)) {
      setErrorMessage(
        "Enter a public GitHub repository URL in the form https://github.com/owner/repository.",
      );
      return;
    }
    if (!profile) {
      setErrorMessage("Choose a persona, or describe your own, before analyzing.");
      return;
    }
    setBusy(true);
    setErrorMessage(null);
    setRepoId(undefined);
    setTourId(undefined);
    setStore(initialSessionState);
    try {
      if (isCustom) await structureCustomPersona();
      const created = await api.createRepo(repoUrl.trim());
      setUsage(await api.getAccountUsage());
      setRepoId(created.repo_id);
      // History is a convenience, not part of the analyze path: if the tour
      // cannot be recorded the session still works, just unsaved.
      void api
        .createTour(created.repo_id, profile, repositoryName(repoUrl))
        .then(async ({ tour_id }) => {
          setTourId(tour_id);
          setTours(await api.listTours());
        })
        .catch(() => undefined);
      setStore((current) =>
        applyRepoStatus(current, {
          status: created.status,
          progress: created.status === "ready" ? 100 : 5,
        }),
      );
      window.history.replaceState(
        null,
        "",
        `/?repo=${encodeURIComponent(created.repo_id)}&persona=${personaId}`,
      );
    } catch (error) {
      if (error instanceof ApiError && error.code === "PROVIDER_KEY_REQUIRED") {
        setProviderDialogOpen(true);
      }
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to reach the RepoPilot API.",
      );
    } finally {
      setBusy(false);
    }
  };

  const askAnything = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!repoId || !askPrompt.trim() || asking) return;
    // An answer with no persona is a different product. The only way to get
    // here without one is "Something else" left blank, so say that instead of
    // silently asking unpersonalized.
    if (!profile) {
      setErrorMessage("Choose a persona, or describe your own, before asking.");
      return;
    }
    setAsking(true);
    setErrorMessage(null);
    try {
      const question = askPrompt.trim();
      const answer = await api.askRepo(repoId, question, profile);
      setUsage(await api.getAccountUsage());
      setStore((current) =>
        appendExchange(current, {
          question,
          answer: answer.answer,
          claims: answer.claims,
          personaLabel: personaLabel(profile),
          repoId,
        }),
      );
      setAskPrompt("");
      if (tourId) {
        void api
          .appendTourMessage(tourId, {
            question,
            answer: answer.answer,
            claims: answer.claims,
            persona_label: personaLabel(profile),
          })
          .catch(() => undefined);
      }
    } catch (error) {
      if (error instanceof ApiError && error.code === "PROVIDER_KEY_REQUIRED") {
        setProviderDialogOpen(true);
      }
      setErrorMessage(error instanceof Error ? error.message : "Unable to query this snapshot.");
    } finally {
      setAsking(false);
    }
  };

  const resumeTour = async (id: string) => {
    setErrorMessage(null);
    try {
      const tour = await api.getTour(id);
      // Fetch the snapshot status up front: the workspace only opens once the
      // repo reads as ready, and without this the resumed tour flashes the
      // onboarding screen ("Not started") until the 1.5s status poll lands.
      const status = await api.getRepoStatus(tour.repo_id).catch(() => undefined);
      const preset = tour.intent_profile
        ? PERSONAS.find((persona) => persona.profile.raw_text === tour.intent_profile?.raw_text)
        : undefined;
      if (preset) {
        setPersonaId(preset.id);
        setCustomProfile(null);
        setCustomText("");
      } else if (tour.intent_profile) {
        setPersonaId(CUSTOM_PERSONA_ID);
        setCustomProfile(tour.intent_profile);
        setCustomText(tour.intent_profile.raw_text);
      }
      setTourId(tour.tour_id);
      setRepoId(tour.repo_id);
      setRepoUrl(`https://github.com/${decodeURIComponent(tour.repo_id)}`);
      const restored = hydrateFromTour(tour);
      setStore(status ? applyRepoStatus(restored, status) : restored);
      window.history.replaceState(null, "", `/?repo=${encodeURIComponent(tour.repo_id)}`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not reopen this tour.");
    }
  };

  const removeTour = async (id: string) => {
    try {
      await api.deleteTour(id);
      setTours((current) => current.filter((tour) => tour.tour_id !== id));
      if (tourId === id) setTourId(undefined);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Could not delete this tour.");
    }
  };

  const connectProvider = async (groqKey: string, huggingfaceKey: string) => {
    setProviderSaving(true);
    setProviderError(null);
    try {
      const nextUsage = await api.connectProvider(groqKey.trim(), huggingfaceKey.trim());
      setUsage(nextUsage);
      setProviderDialogOpen(false);
      setErrorMessage(null);
    } catch (error) {
      setProviderError(error instanceof Error ? error.message : "Could not connect these keys.");
    } finally {
      setProviderSaving(false);
    }
  };

  const disconnectProvider = async () => {
    setProviderSaving(true);
    setProviderError(null);
    try {
      setUsage(await api.disconnectProvider());
      setProviderDialogOpen(false);
    } catch (error) {
      setProviderError(error instanceof Error ? error.message : "Could not disconnect these keys.");
    } finally {
      setProviderSaving(false);
    }
  };

  const personaPicker = (
    <div className="persona-picker">
      <div className="persona-grid" role="group" aria-label="Answer persona">
        {PERSONAS.map((persona) => {
          const active = personaId === persona.id;
          return (
            <button
              key={persona.id}
              type="button"
              className="persona-option"
              data-active={active}
              aria-pressed={active}
              onClick={() => setPersonaId(persona.id)}
            >
              <span className="option-check" aria-hidden="true">
                {active ? <CheckCircle size={19} weight="fill" /> : null}
              </span>
              <span>
                <strong>{persona.label}</strong>
                <small>{persona.blurb}</small>
              </span>
            </button>
          );
        })}
        <button
          type="button"
          className="persona-option"
          data-active={isCustom}
          aria-pressed={isCustom}
          onClick={() => setPersonaId(CUSTOM_PERSONA_ID)}
        >
          <span className="option-check" aria-hidden="true">
            {isCustom ? <CheckCircle size={19} weight="fill" /> : null}
          </span>
          <span>
            <strong>Something else</strong>
            <small>Describe who you are and what you need.</small>
          </span>
        </button>
      </div>

      {isCustom ? (
        <div className="feature-field">
          <label htmlFor="persona-custom">Who are you, and what do you want from this repo?</label>
          <input
            id="persona-custom"
            className="text-input"
            value={customText}
            onChange={(event) => {
              setCustomText(event.target.value);
              setCustomProfile(null);
            }}
            onBlur={() => void structureCustomPersona()}
            placeholder="I'm writing a migration guide and need the breaking changes"
          />
          <p className="field-help">
            {draftingIntent
              ? "Reading your description…"
              : customProfile
                ? `Lens: ${personaLabel(customProfile)}`
                : "Answers will be shaped around this description."}
          </p>
        </div>
      ) : null}
    </div>
  );

  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="product-brand" href="/" aria-label="RepoPilot home">
          <span className="brand-symbol" aria-hidden="true">
            <GitBranch size={19} weight="bold" />
          </span>
          <span>RepoPilot</span>
        </a>
        <div className="header-controls">
          <button
            className="usage-control"
            type="button"
            onClick={() => setProviderDialogOpen(true)}
          >
            <LockKey
              size={17}
              weight={usage?.provider_connected ? "fill" : "regular"}
              aria-hidden="true"
            />
            <span>
              {usage?.provider_connected ? "Your provider is connected" : "Connect your provider"}
            </span>
          </button>
          {viewer ? (
            <form action={signOutAction} className="account-control">
              <span className="account-name">{viewer.name ?? "Signed in"}</span>
              <button className="usage-control" type="submit">
                <SignOut size={17} aria-hidden="true" />
                <span>Sign out</span>
              </button>
            </form>
          ) : null}
        </div>
      </header>

      {!inWorkspace ? (
        <div className="onboarding-layout">
          <section className="onboarding-intro" aria-labelledby="onboarding-title">
            <div>
              <p className="section-kicker">Repository onboarding</p>
              <h1 id="onboarding-title">Ask a codebase anything, as anyone.</h1>
              <p className="intro-copy">
                Paste a repository, pick the lens you are reading through, and ask. The same
                verified facts get prioritized differently for a contributor, a competitor, or a
                security reviewer.
              </p>
            </div>

            <div className="product-principles" aria-label="How RepoPilot works">
              <div className="principle-row">
                <UserFocus size={21} aria-hidden="true" />
                <div>
                  <strong>Answers shaped by your purpose</strong>
                  <span>Your persona decides which findings lead.</span>
                </div>
              </div>
              <div className="principle-row">
                <ShieldCheck size={21} aria-hidden="true" />
                <div>
                  <strong>Verified source claims</strong>
                  <span>Every factual claim links back to a concrete file range.</span>
                </div>
              </div>
              <div className="principle-row">
                <MagnifyingGlass size={21} aria-hidden="true" />
                <div>
                  <strong>Repository-specific retrieval</strong>
                  <span>Answers stay scoped to the indexed snapshot.</span>
                </div>
              </div>
            </div>

            {tours.length > 0 ? (
              <div className="tour-history" aria-label="Your tours">
                <span className="section-kicker">Your tours</span>
                <ul>
                  {tours.map((tour) => (
                    <li key={tour.tour_id}>
                      <button type="button" onClick={() => void resumeTour(tour.tour_id)}>
                        <strong>{tour.title || decodeURIComponent(tour.repo_id)}</strong>
                        <small>
                          {tour.message_count} question{tour.message_count === 1 ? "" : "s"} ·{" "}
                          {new Date(tour.updated_at).toLocaleDateString()}
                        </small>
                      </button>
                      <button
                        className="icon-button"
                        type="button"
                        onClick={() => void removeTour(tour.tour_id)}
                        aria-label={`Delete tour for ${decodeURIComponent(tour.repo_id)}`}
                      >
                        <Trash size={16} />
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <p className="scope-note">
              Supports Python, TypeScript, JavaScript, Java, Go, Rust, C-family languages, Ruby,
              PHP, Swift, Scala, Vue, Svelte, Kotlin, and shell repositories.
            </p>
          </section>

          <section className="setup-panel" aria-label="Configure repository session">
            <form className="repo-form" onSubmit={submitRepo} noValidate>
              <div className="setup-heading">
                <div>
                  <span className="step-label">Repository</span>
                  <h2>Choose a codebase</h2>
                </div>
                {repoId ? (
                  <span className={`repo-status repo-status-${store.repoStatus?.status ?? "queued"}`}>
                    {repoReady ? <CheckCircle size={16} weight="fill" /> : <ClockCountdown size={16} />}
                    {statusLabel(store.repoStatus?.status)}
                  </span>
                ) : null}
              </div>

              <label htmlFor="repo-url">Public GitHub URL</label>
              <div className="repo-input-row">
                <span className="input-icon" aria-hidden="true">
                  <GithubLogo size={20} />
                </span>
                <input
                  id="repo-url"
                  className="text-input repo-input"
                  type="url"
                  autoComplete="url"
                  value={repoUrl}
                  onChange={(event) => setRepoUrl(event.target.value)}
                  placeholder="https://github.com/owner/repository"
                  aria-describedby="repo-help"
                />
              </div>
              <p id="repo-help" className="field-help">
                RepoPilot indexes the current default branch. Private repositories are not
                supported.
              </p>

              <div className="setup-divider" />

              <div className="setup-heading goal-heading">
                <div>
                  <span className="step-label">Lens</span>
                  <h2>Who is asking?</h2>
                </div>
              </div>

              {personaPicker}

              {errorMessage ? (
                <div className="inline-alert" role="alert">
                  <WarningCircle size={19} weight="fill" aria-hidden="true" />
                  <span>{errorMessage}</span>
                </div>
              ) : null}

              {repoId ? (
                <div className="index-status" aria-live="polite">
                  <div className="index-status-header">
                    <div>
                      <strong>{repoDisplayName}</strong>
                      <span>{statusLabel(store.repoStatus?.status)}</span>
                    </div>
                    <span className="progress-value">{progress}%</span>
                  </div>
                  <div
                    className="progress-track"
                    role="progressbar"
                    aria-label="Repository indexing progress"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={progress}
                  >
                    <span className="progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                  <p>
                    {store.firstImpression ||
                      "Cloning files, creating chunks, and building the repository graph."}
                  </p>
                </div>
              ) : null}

              <div className="setup-footer">
                <div className="intent-summary">
                  <span>Answering as</span>
                  <strong>{personaLabel(profile)}</strong>
                </div>
                <button
                  className="button button-primary start-button"
                  type="submit"
                  disabled={busy || Boolean(repoId && !repoError)}
                >
                  {busy ? "Analyzing" : repoId && !repoError ? "Indexing" : "Analyze and ask"}
                  {!busy && !repoId ? (
                    <ArrowRight size={17} weight="bold" aria-hidden="true" />
                  ) : null}
                </button>
              </div>
            </form>
          </section>
        </div>
      ) : (
        <div className="workspace">
          <header className="workspace-header">
            <div className="workspace-title">
              <button
                className="icon-button"
                type="button"
                onClick={() => {
                  setRepoId(undefined);
                  setTourId(undefined);
                  setStore(initialSessionState);
                  window.history.replaceState(null, "", "/");
                  void api.listTours().then(setTours).catch(() => undefined);
                }}
                aria-label="Back to repository setup"
              >
                <ArrowLeft size={19} />
              </button>
              <div>
                <span>{repoDisplayName}</span>
                <h1>Ask this repository</h1>
              </div>
            </div>
            <div className="workspace-meta">
              <span className="repo-status repo-status-ready">
                <CheckCircle size={16} weight="fill" aria-hidden="true" />
                Snapshot ready
              </span>
            </div>
          </header>

          {errorMessage || store.error ? (
            <div className="workspace-alert inline-alert" role="alert">
              <WarningCircle size={19} weight="fill" aria-hidden="true" />
              <span>{errorMessage || store.error}</span>
            </div>
          ) : null}

          <div className="workspace-grid">
            <aside className="tour-navigation" aria-label="Session lens">
              <div className="navigation-heading">
                <UserFocus size={18} aria-hidden="true" />
                <span>Answering as</span>
              </div>
              {/* The lens is switchable mid-session: ask the same question
                  again as someone else and compare the two answers. */}
              {personaPicker}
              <div className="navigation-focus">
                <span>Priorities</span>
                <div className="keyword-list">
                  {(profile?.focus_keywords ?? []).map((keyword) => (
                    <span key={keyword}>{keyword}</span>
                  ))}
                </div>
              </div>
            </aside>

            <section className="tour-content" aria-label="Answers" aria-live="polite">
              {store.firstImpression ? (
                <p className="first-impression">{store.firstImpression}</p>
              ) : null}

              <form className="ask-panel" onSubmit={askAnything}>
                <div className="ask-heading">
                  <label htmlFor="ask-repository">Ask this repository</label>
                  <button type="button" onClick={() => setProviderDialogOpen(true)}>
                    <LockKey size={15} aria-hidden="true" />
                    {usage?.provider_connected ? "Using your provider" : "Using the shared key"}
                  </button>
                </div>
                <div className="ask-row">
                  <input
                    id="ask-repository"
                    className="text-input ask-input"
                    value={askPrompt}
                    onChange={(event) => setAskPrompt(event.target.value)}
                    placeholder="What is the tech stack?"
                    disabled={asking}
                  />
                  <button
                    className="button button-primary ask-button"
                    type="submit"
                    disabled={!askPrompt.trim() || asking}
                  >
                    <PaperPlaneTilt size={18} weight="fill" aria-hidden="true" />
                    {asking ? "Asking" : "Ask"}
                  </button>
                </div>
                <p>
                  Answers use only the indexed snapshot, include source references, and are
                  prioritized for {personaLabel(profile)}.
                </p>
              </form>

              {store.exchanges.length === 0 ? (
                <div className="answers-empty">
                  <MagnifyingGlass size={26} aria-hidden="true" />
                  <strong>Ask your first question</strong>
                  <span>
                    Answers are drawn from the indexed snapshot and prioritized for the lens you
                    picked.
                  </span>
                </div>
              ) : (
                [...store.exchanges].reverse().map((exchange) => (
                  <article className="tour-section" id={`answer-${exchange.id}`} key={exchange.id}>
                    <div className="tour-section-heading">
                      <h2>{exchange.question}</h2>
                      <span className="section-complete">
                        <UserFocus size={15} aria-hidden="true" />
                        {exchange.personaLabel}
                      </span>
                    </div>
                    <AnswerBody text={exchange.answer} />

                    {exchange.claimIds.length > 0 ? (
                      <div className="claim-group" aria-label={`Sources for ${exchange.question}`}>
                        <div className="claim-group-label">Verified sources</div>
                        {exchange.claimIds.map((claimId) => {
                          const claim = store.claimsById[claimId];
                          const flagged = claim.status === "flagged" || claim.status === "rejected";
                          const unverified = claim.status === "unverified";
                          return (
                            <button
                              key={claimId}
                              type="button"
                              className="claim-row"
                              data-active={store.selectedClaimId === claimId}
                              data-flagged={flagged}
                              data-unverified={unverified}
                              onClick={() => setStore((current) => selectClaim(current, claimId))}
                            >
                              <span className="claim-icon" aria-hidden="true">
                                {flagged || unverified ? (
                                  <WarningCircle size={19} weight="fill" />
                                ) : (
                                  <ShieldCheck size={19} weight="fill" />
                                )}
                              </span>
                              <span className="claim-content">
                                <strong>{claim.text}</strong>
                                <span className="claim-reference">
                                  {claim.refs[0].file_path}:{claim.refs[0].start_line}-
                                  {claim.refs[0].end_line}
                                </span>
                                {claim.verifier_note ? <small>{claim.verifier_note}</small> : null}
                              </span>
                              <span className={claimBadgeClass(claim.status)}>
                                {claimBadgeLabel(claim.status)}
                              </span>
                            </button>
                          );
                        })}
                        {/* One panel per exchange, following the selected claim
                            when the selection is one of this exchange's — so
                            clicking a row changes what the panel expands rather
                            than only restyling it. Falls back to the first claim
                            that names a symbol: the graph is keyed by symbol, and
                            a claim whose ref has none has nothing to look up. */}
                        {(() => {
                          const selected = store.selectedClaimId;
                          const ordered =
                            selected && exchange.claimIds.includes(selected)
                              ? [selected, ...exchange.claimIds]
                              : exchange.claimIds;
                          const anchor = ordered
                            .map((id) => store.claimsById[id]?.refs[0]?.symbol)
                            .find((symbol): symbol is string => Boolean(symbol));
                          // Keyed so a new anchor remounts: the panel caches the
                          // neighbours it fetched, and without this it would keep
                          // showing the previous claim's.
                          return anchor && repoId ? (
                            <GraphNeighbours key={anchor} repoId={repoId} symbol={anchor} />
                          ) : null;
                        })()}
                      </div>
                    ) : null}
                  </article>
                ))
              )}

            </section>

          </div>
        </div>
      )}
      <ProviderDialog
        error={providerError}
        onClose={() => {
          setProviderDialogOpen(false);
          setProviderError(null);
        }}
        onConnect={connectProvider}
        onDisconnect={disconnectProvider}
        open={providerDialogOpen}
        saving={providerSaving}
        usage={usage}
      />
    </main>
  );
}

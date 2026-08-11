"use client";

import {
  ArrowRight,
  CaretDown,
  ChatCircleText,
  CheckCircle,
  ClockCountdown,
  Eye,
  EyeSlash,
  FileCode,
  GitBranch,
  GithubLogo,
  List,
  LockKey,
  MagnifyingGlass,
  PaperPlaneTilt,
  Plus,
  ShieldCheck,
  SignOut,
  Trash,
  UserFocus,
  WarningCircle,
  X,
} from "@phosphor-icons/react";
import { type FormEvent, useEffect, useMemo, useReducer, useRef, useState } from "react";

import { ClaimRow } from "./claim-row";
import { GraphNeighbours } from "./graph-neighbours";
import {
  ApiError,
  api,
  type AccountUsage,
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
  chatTitle,
  hydrateFromTour,
  initialSessionState,
  personaLabel,
  selectClaim,
  type SessionState,
} from "@/lib/session-store";

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

/** Render one answer line: `backticked` spans become code, "[3]" citation
 *  markers become superscripts. The claim list below the answer carries the
 *  actual source links. */
function AnswerLine({ text }: { text: string }) {
  // Splitting on both patterns at once keeps a citation that lands inside a
  // code span from being swallowed by it.
  const parts = text.split(/(`[^`]+`|\[\d+\])/g).filter(Boolean);
  return (
    <>
      {parts.map((part, index) => {
        if (/^\[\d+\]$/.test(part)) {
          return (
            <sup className="answer-citation" key={index}>
              {part.slice(1, -1)}
            </sup>
          );
        }
        if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
          return (
            <code className="answer-code" key={index}>
              {part.slice(1, -1)}
            </code>
          );
        }
        return <span key={index}>{part}</span>;
      })}
    </>
  );
}

/** Render the answer body: "## " lines become headings, everything else is a
 *  claim line. The first section is the direct answer to the question, so it
 *  is styled to lead rather than reading like one more detail. */
function AnswerBody({ text }: { text: string }) {
  const lines = text.split("\n").filter((line) => line.trim().length > 0);
  let sectionIndex = -1;
  return (
    <div className="section-body answer-body">
      {lines.map((line, index) => {
        const trimmed = line.trim();
        if (trimmed.startsWith("#")) {
          sectionIndex += 1;
          return (
            <h3 className="answer-heading" key={index}>
              {trimmed.replace(/^#+\s*/, "")}
            </h3>
          );
        }
        const body = trimmed.replace(/^[-•*]\s*/, "");
        return (
          <p className="answer-line" data-lead={sectionIndex === 0} key={index}>
            <AnswerLine text={body} />
          </p>
        );
      })}
    </div>
  );
}

/** Types a line out and erases it, on a loop — the empty workspace has
 *  nothing moving in it otherwise. Static for anyone who asked for less
 *  motion. */
function Typewriter({ text }: { text: string }) {
  const [shown, setShown] = useState(text);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let length = 0;
    let erasing = false;
    setShown("");
    const timer = window.setInterval(() => {
      if (!erasing && length === text.length) {
        // Hold the finished line for a beat before erasing it.
        erasing = true;
        return;
      }
      if (erasing && length === 0) {
        erasing = false;
        return;
      }
      length += erasing ? -1 : 1;
      setShown(text.slice(0, length));
    }, 90);
    return () => window.clearInterval(timer);
  }, [text]);

  return (
    <strong>
      {shown}
      <span className="answer-caret" aria-hidden="true" />
    </strong>
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
  // The answer as it generates, before claims and verification land.
  const [streaming, setStreaming] = useState<{ question: string; text: string } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [usage, setUsage] = useState<AccountUsage | null>(null);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [providerSaving, setProviderSaving] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [store, setStore] = useState<SessionState>(initialSessionState);
  const [tours, setTours] = useState<TourSummary[]>([]);
  const [tourId, setTourId] = useState<string>();
  // The chat drawer, opened from the hamburger in the app header.
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [personaMenuOpen, setPersonaMenuOpen] = useState(false);
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

  // Escape closes the drawer, matching the dialog it visually behaves like.
  useEffect(() => {
    if (!sidebarOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sidebarOpen]);

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
      // No tour yet: a chat is created by the first question, so it can be
      // named after it. Indexing a repo and never asking leaves no empty chat.
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
      if (
        error instanceof ApiError &&
        (error.code === "PROVIDER_KEY_REQUIRED" || error.code === "PROVIDER_KEY_REJECTED")
      ) {
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
    // Providers emit tokens in bursts of wildly uneven size — a whole
    // paragraph can land in one frame, and the keyword-match fallback returns
    // the answer in a single piece with no tokens at all. Queue whatever
    // arrives and release it a word at a time so every answer types out.
    const queue: string[] = [];
    let shown = "";
    const words = (text: string) => text.match(/\S+\s*|\s+/g) ?? [];
    // Follow the answer as it types, but only while the reader is already at
    // the end of it — scrolling up to re-read an earlier answer must not be
    // yanked back down.
    const followBottom = (force = false) => {
      const distance =
        document.documentElement.scrollHeight - window.innerHeight - window.scrollY;
      if (!force && distance > 200) return;
      requestAnimationFrame(() =>
        window.scrollTo({
          top: document.documentElement.scrollHeight,
          behavior: force ? "smooth" : "auto",
        }),
      );
    };
    const ticker = window.setInterval(() => {
      if (queue.length === 0) return;
      // One word normally; a long backlog catches up rather than lagging
      // minutes behind an answer that has already fully arrived.
      const next = queue.splice(0, queue.length > 150 ? 3 : 1).join("");
      shown += next;
      setStreaming((current) => (current ? { ...current, text: current.text + next } : current));
      followBottom();
    }, 18);
    const drained = () =>
      new Promise<void>((resolve) => {
        const poll = window.setInterval(() => {
          if (queue.length > 0) return;
          window.clearInterval(poll);
          resolve();
        }, 30);
      });
    try {
      const question = askPrompt.trim();
      setStreaming({ question, text: "" });
      // Asking from halfway up the history should land on the new answer.
      followBottom(true);
      const answer = await api.askRepoStreaming(repoId, question, profile, (token) => {
        // Each entry keeps its own trailing whitespace, so newlines and the
        // spacing between words survive the split.
        queue.push(...words(token));
      });
      // Type out whatever the stream did not deliver — the whole answer when
      // it never streamed — instead of snapping to the finished text.
      if (answer.answer.startsWith(shown)) {
        queue.push(...words(answer.answer.slice(shown.length)));
      } else {
        queue.length = 0;
        shown = "";
        setStreaming({ question, text: "" });
        queue.push(...words(answer.answer));
      }
      await drained();
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
      // History is a convenience, not part of the ask path: if the chat cannot
      // be recorded the answer still stands, just unsaved.
      void (async () => {
        let chatId = tourId;
        if (!chatId) {
          chatId = (await api.createTour(repoId, profile, chatTitle(question))).tour_id;
          setTourId(chatId);
        }
        await api.appendTourMessage(chatId, {
          question,
          answer: answer.answer,
          claims: answer.claims,
          persona_label: personaLabel(profile),
        });
        // Keep the sidebar's titles and question counts honest.
        setTours(await api.listTours());
      })().catch(() => undefined);
    } catch (error) {
      if (
        error instanceof ApiError &&
        (error.code === "PROVIDER_KEY_REQUIRED" || error.code === "PROVIDER_KEY_REJECTED")
      ) {
        setProviderDialogOpen(true);
      }
      setErrorMessage(error instanceof Error ? error.message : "Unable to query this snapshot.");
    } finally {
      window.clearInterval(ticker);
      setAsking(false);
      setStreaming(null);
    }
  };

  const resumeTour = async (id: string) => {
    setErrorMessage(null);
    setSidebarOpen(false);
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

  // Both the card grid and the phone disclosure list offer the same choices,
  // "Something else" included.
  const personaChoices = [
    ...PERSONAS.map((persona) => ({
      id: persona.id,
      label: persona.label,
      blurb: persona.blurb,
    })),
    {
      id: CUSTOM_PERSONA_ID,
      label: "Something else",
      blurb: "Describe who you are and what you need.",
    },
  ];
  const chosenPersona =
    personaChoices.find((choice) => choice.id === personaId) ?? personaChoices[0];

  const personaOption = (choice: (typeof personaChoices)[number], onPick: () => void) => {
    const active = personaId === choice.id;
    return (
      <button
        key={choice.id}
        type="button"
        className="persona-option"
        data-active={active}
        aria-pressed={active}
        onClick={onPick}
      >
        <span className="option-check" aria-hidden="true">
          {active ? <CheckCircle size={19} weight="fill" /> : null}
        </span>
        <span>
          <strong>{choice.label}</strong>
          <small>{choice.blurb}</small>
        </span>
      </button>
    );
  };

  const personaPicker = (
    <div className="persona-picker">
      {/* Seven cards is two screens of scrolling on a phone. A disclosure keeps
          the list to one row until it is wanted — and unlike a native <select>
          the open list is ours to style, so it matches the theme. The grid
          takes over again from 680px up. */}
      <details
        className="persona-dropdown"
        open={personaMenuOpen}
        onToggle={(event) => setPersonaMenuOpen(event.currentTarget.open)}
      >
        <summary>
          <span>
            <strong>{chosenPersona.label}</strong>
            <small>{chosenPersona.blurb}</small>
          </span>
          <CaretDown size={16} weight="bold" aria-hidden="true" />
        </summary>
        <div className="persona-menu" role="group" aria-label="Who is asking">
          {personaChoices.map((choice) =>
            personaOption(choice, () => {
              setPersonaId(choice.id);
              setPersonaMenuOpen(false);
            }),
          )}
        </div>
      </details>

      <div className="persona-grid" role="group" aria-label="Answer persona">
        {personaChoices.map((choice) => personaOption(choice, () => setPersonaId(choice.id)))}
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

  // Compact lens control for the workspace: the sidebar is the chat session
  // list now, so the persona lives under the ask box as a plain <select>.
  const personaSelect = (
    <div className="ask-persona">
      <label htmlFor="ask-persona-select">
        <UserFocus size={15} aria-hidden="true" />
        Answering as
      </label>
      <select
        id="ask-persona-select"
        className="text-input"
        value={personaId}
        onChange={(event) => setPersonaId(event.target.value)}
      >
        {PERSONAS.map((persona) => (
          <option key={persona.id} value={persona.id}>
            {persona.label}
          </option>
        ))}
        <option value={CUSTOM_PERSONA_ID}>Something else…</option>
      </select>
      {isCustom ? (
        <input
          className="text-input"
          value={customText}
          onChange={(event) => {
            setCustomText(event.target.value);
            setCustomProfile(null);
          }}
          onBlur={() => void structureCustomPersona()}
          placeholder="I'm writing a migration guide and need the breaking changes"
          aria-label="Describe who you are and what you need"
        />
      ) : null}
    </div>
  );

  /** Leave the workspace entirely, back to repository setup. */
  const leaveWorkspace = () => {
    setRepoId(undefined);
    setTourId(undefined);
    setStore(initialSessionState);
    window.history.replaceState(null, "", "/");
    void api.listTours().then(setTours).catch(() => undefined);
  };

  /** Blank conversation on the same snapshot — the reader stays put, and the
   *  next question opens (and names) a fresh chat. */
  const startNewChat = () => {
    setSidebarOpen(false);
    setTourId(undefined);
    setAskPrompt("");
    setErrorMessage(null);
    setStore((current) => ({
      ...initialSessionState,
      repoStatus: current.repoStatus,
      firstImpression: current.firstImpression,
    }));
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <button
          className="icon-button sidebar-toggle"
          type="button"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open chats"
          aria-expanded={sidebarOpen}
          aria-controls="chat-sidebar"
        >
          <List size={19} />
        </button>
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

      {/* Every saved chat, newest first, one hamburger away from anywhere in
          the app — including the setup screen, so reopening a repository that
          is already indexed never goes through indexing again. */}
      {sidebarOpen ? (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close chats"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}
      <aside
        className="tour-navigation"
        id="chat-sidebar"
        data-open={sidebarOpen}
        aria-label="Chat sessions"
      >
        <button
          className="new-chat-button"
          type="button"
          onClick={inWorkspace ? startNewChat : () => setSidebarOpen(false)}
        >
          <Plus size={15} weight="bold" aria-hidden="true" />
          New chat
        </button>
        {inWorkspace ? (
          <button className="new-chat-button" type="button" onClick={leaveWorkspace}>
            <GithubLogo size={15} aria-hidden="true" />
            Another repository
          </button>
        ) : null}
        <div className="navigation-heading">
          <ChatCircleText size={18} aria-hidden="true" />
          <span>Chats</span>
          <button
            className="icon-button sidebar-close"
            type="button"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close chats"
          >
            <X size={16} />
          </button>
        </div>
        {tours.length === 0 ? (
          <p className="navigation-empty">
            Your chats appear here once you ask a repository something.
          </p>
        ) : (
          <ul className="chat-list">
            {tours.map((tour) => (
              <li key={tour.tour_id} data-active={tour.tour_id === tourId}>
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
                  aria-label={`Delete chat for ${decodeURIComponent(tour.repo_id)}`}
                >
                  <Trash size={15} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </aside>

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

          {errorMessage || store.error ? (
            <div className="workspace-alert inline-alert" role="alert">
              <WarningCircle size={19} weight="fill" aria-hidden="true" />
              <span>{errorMessage || store.error}</span>
            </div>
          ) : null}

          <section className="tour-content" aria-label="Answers" aria-live="polite">
              {store.firstImpression ? (
                <p className="first-impression">{store.firstImpression}</p>
              ) : null}

              {store.exchanges.length === 0 && !streaming ? (
                <div className="answers-empty">
                  <MagnifyingGlass size={26} aria-hidden="true" />
                  <Typewriter text="Ask your first question" />
                  <span>
                    Answers are drawn from the indexed snapshot and prioritized for the lens you
                    picked.
                  </span>
                </div>
              ) : (
                store.exchanges.map((exchange) => (
                  <article className="tour-section" id={`answer-${exchange.id}`} key={exchange.id}>
                    <div className="tour-section-heading">
                      <h2>{exchange.question}</h2>
                      <span className="section-complete">
                        <UserFocus size={15} aria-hidden="true" />
                        {exchange.personaLabel}
                      </span>
                    </div>
                    <AnswerBody text={exchange.answer} />

                    {/* The API degrades to keyword matching whenever the model
                        call raises, and puts the reason in retrieval_path.
                        Showing it turns "the model could not answer" from a
                        mystery into something actionable. */}
                    {(() => {
                      const reason = exchange.claimIds
                        .flatMap((claimId) => store.claimsById[claimId]?.retrieval_path ?? [])
                        .find((entry) => entry.startsWith("rag_fallback:"));
                      return reason ? (
                        <p className="fallback-reason">
                          <WarningCircle size={15} weight="fill" aria-hidden="true" />
                          Model call failed: {reason.slice("rag_fallback:".length)}
                        </p>
                      ) : null;
                    })()}

                    {/* Folded by default: the answer is the thing being read,
                        and a dozen source rows between two answers is a wall
                        to scroll past. */}
                    {exchange.claimIds.length > 0 ? (
                      <details
                        className="claim-group"
                        aria-label={`Sources for ${exchange.question}`}
                      >
                        <summary className="claim-group-label">
                          <CaretDown size={13} weight="bold" aria-hidden="true" />
                          Verified sources
                          <span className="claim-group-count">{exchange.claimIds.length}</span>
                        </summary>
                        {exchange.claimIds.map((claimId) => (
                          <ClaimRow
                            key={claimId}
                            claim={store.claimsById[claimId]}
                            active={store.selectedClaimId === claimId}
                            onSelect={() =>
                              setStore((current) => selectClaim(current, claimId))
                            }
                          />
                        ))}
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
                      </details>
                    ) : null}
                  </article>
                ))
              )}
              {streaming ? (
                <article className="tour-section tour-section-streaming">
                  <div className="tour-section-heading">
                    <h2>{streaming.question}</h2>
                    <span className="section-complete">
                      <UserFocus size={15} aria-hidden="true" />
                      {personaLabel(profile)}
                    </span>
                  </div>
                  {streaming.text ? (
                    <AnswerBody text={streaming.text} />
                  ) : (
                    <p className="answer-line answer-pending">Reading the snapshot…</p>
                  )}
                  <span className="answer-caret" aria-hidden="true" />
                </article>
              ) : null}

            {/* Pinned to the bottom, the way a chat composer is: the box, the
                repo-level module map, and the lens answers come through.
                Everything else that used to sit up here was commentary. */}
            <form className="ask-panel" onSubmit={askAnything}>
              <div className="ask-row">
                <input
                  id="ask-repository"
                  className="text-input ask-input"
                  value={askPrompt}
                  onChange={(event) => setAskPrompt(event.target.value)}
                  placeholder="What is the tech stack?"
                  aria-label="Ask this repository"
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
              <div className="ask-tools">{personaSelect}</div>
            </form>
          </section>
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

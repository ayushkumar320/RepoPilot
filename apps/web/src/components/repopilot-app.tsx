"use client";

import {
  ArrowLeft,
  ArrowRight,
  BookOpenText,
  CaretRight,
  CheckCircle,
  ClockCountdown,
  Eye,
  EyeSlash,
  FileCode,
  GitBranch,
  GithubLogo,
  ListBullets,
  LockKey,
  MagnifyingGlass,
  PaperPlaneTilt,
  ShieldCheck,
  WarningCircle,
  Wrench,
  X,
} from "@phosphor-icons/react";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useReducer, useState } from "react";

import {
  ApiError,
  api,
  type AccountUsage,
  type ClaimEvent,
  type ClaimStatus,
  type IntentProfile,
  type RepoStatus,
  type TourEvent,
} from "@/lib/api/generated";
import {
  appendAnswerAsSection,
  applyRepoStatus,
  applyTourEvent,
  hydrateViewer,
  initialTourStoreState,
  selectClaim,
  type TourStoreState,
} from "@/lib/tour-store";

type LearnChoice = "overall structure" | "specific feature" | "data model";
type ContributeChoice =
  | "fix a reported issue"
  | "improve code quality"
  | "hunt for likely problems"
  | "show all, ranked";
type Mode = "learn" | "contribute";

interface ViewerLine {
  active: boolean;
  content: string;
  number: number;
}

const learnChoices: Array<{ value: LearnChoice; label: string; description: string }> = [
  {
    value: "overall structure",
    label: "System overview",
    description: "Map entry points, modules, and the main execution path.",
  },
  {
    value: "specific feature",
    label: "Specific feature",
    description: "Trace one capability from its public surface into the implementation.",
  },
  {
    value: "data model",
    label: "Data model",
    description: "Follow state, schemas, persistence, and ownership boundaries.",
  },
];

const contributeChoices: Array<{
  value: ContributeChoice;
  label: string;
  description: string;
}> = [
  {
    value: "fix a reported issue",
    label: "Fix an issue",
    description: "Find the likely change surface and the tests that protect it.",
  },
  {
    value: "improve code quality",
    label: "Improve quality",
    description: "Prioritize maintainability, coverage, and structural friction.",
  },
  {
    value: "hunt for likely problems",
    label: "Investigate risk",
    description: "Surface guarded suspicions with concrete confirmation steps.",
  },
  {
    value: "show all, ranked",
    label: "Rank opportunities",
    description: "Compare issue, quality, and risk-oriented contribution paths.",
  },
];

function parseSseFrame(chunk: string): TourEvent[] {
  const frames = chunk.split("\n\n").filter(Boolean);
  const events: TourEvent[] = [];
  for (const frame of frames) {
    const lines = frame.split("\n");
    let eventName = "";
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      }
      if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }
    if (eventName && dataLines.length > 0) {
      events.push(JSON.parse(dataLines.join("\n")) as TourEvent);
    }
  }
  return events;
}

function buildProfile(
  mode: Mode,
  learnChoice: LearnChoice,
  contributeChoice: ContributeChoice,
  featureText: string,
): IntentProfile {
  if (mode === "learn") {
    const focus =
      learnChoice === "specific feature" && featureText.trim()
        ? [featureText.trim()]
        : [learnChoice];
    return {
      raw_text:
        learnChoice === "specific feature" && featureText.trim()
          ? `I want to learn the ${featureText.trim()} feature`
          : `I want to learn this codebase through its ${learnChoice}`,
      modality_weights: { understand: 1 },
      focus_keywords: focus,
      audience_framing: "casual contributor",
      output_shape_preference: "narrative",
    };
  }

  const focusKeywords =
    contributeChoice === "hunt for likely problems"
      ? ["fragility", "risk"]
      : contributeChoice === "improve code quality"
        ? ["quality", "testing"]
        : contributeChoice === "fix a reported issue"
          ? ["issues", "bugs"]
          : ["quality", "issues", "risk"];
  return {
    raw_text: `I want to contribute by helping with ${contributeChoice}`,
    modality_weights: { change: 1, evaluate: 0.5 },
    focus_keywords: focusKeywords,
    audience_framing: "hands-on contributor",
    output_shape_preference: "ranked_list",
  };
}

function splitLines(content: string, startLine: number, endLine: number): ViewerLine[] {
  return content.split("\n").map((line, index) => {
    const number = index + startLine;
    return {
      active: number >= startLine && number <= endLine,
      content: line,
      number,
    };
  });
}

function claimBadgeClass(status: ClaimStatus): string {
  return status === "flagged" || status === "rejected"
    ? "status-badge status-badge-warning"
    : "status-badge status-badge-success";
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
    return url.protocol === "https:" && url.hostname === "github.com" && url.pathname.split("/").filter(Boolean).length === 2;
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

  useEffect(() => {
    if (!open) {
      setGroqKey("");
      setHuggingfaceKey("");
      setShowGroq(false);
      setShowHuggingface(false);
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="dialog-backdrop" role="presentation">
      <section
        className="provider-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="provider-dialog-title"
      >
        <div className="dialog-heading">
          <div className="dialog-icon" aria-hidden="true">
            <LockKey size={21} weight="fill" />
          </div>
          <div>
            <h2 id="provider-dialog-title">
              {usage?.provider_connected ? "Provider connected" : "Continue with your Groq limit"}
            </h2>
            <p>
              Keys go directly to the API and remain only in this server session. They are never
              stored in the browser or database.
            </p>
          </div>
          <button className="icon-button dialog-close" type="button" onClick={onClose} aria-label="Close">
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
            <button className="button button-secondary" type="button" disabled={saving} onClick={() => void onDisconnect()}>
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
                <button type="button" onClick={() => setShowGroq((value) => !value)} aria-label={showGroq ? "Hide Groq key" : "Show Groq key"}>
                  {showGroq ? <EyeSlash size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p id="groq-key-help">Required. Usage is charged against your Groq account limits.</p>
            </div>

            <div className="credential-field">
              <label htmlFor="huggingface-api-key">Hugging Face token <span>Optional</span></label>
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
                <button type="button" onClick={() => setShowHuggingface((value) => !value)} aria-label={showHuggingface ? "Hide Hugging Face token" : "Show Hugging Face token"}>
                  {showHuggingface ? <EyeSlash size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <p id="hf-key-help">Used only as a fallback when the Groq request cannot complete.</p>
            </div>

            {error ? <div className="dialog-error" role="alert">{error}</div> : null}

            <div className="dialog-actions">
              <button className="button button-secondary" type="button" onClick={onClose}>Not now</button>
              <button className="button button-primary" type="submit" disabled={saving || groqKey.trim().length < 12}>
                {saving ? "Connecting" : "Connect keys"}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}

export default function RepoPilotApp() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/flask");
  const [repoId, setRepoId] = useState<string>();
  const [tourId, setTourId] = useState<string>();
  const [mode, setMode] = useState<Mode>("learn");
  const [learnChoice, setLearnChoice] = useState<LearnChoice>("overall structure");
  const [contributeChoice, setContributeChoice] =
    useState<ContributeChoice>("improve code quality");
  const [featureText, setFeatureText] = useState("");
  const [askPrompt, setAskPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [asking, setAsking] = useState(false);
  const [viewerLoading, setViewerLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [usage, setUsage] = useState<AccountUsage | null>(null);
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [providerSaving, setProviderSaving] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [stage, setStage] = useState<"capture" | "tour">("capture");
  const [store, setStore] = useState<TourStoreState>(initialTourStoreState);
  const [pollTick, forcePoll] = useReducer((value: number) => value + 1, 0);

  const profile = useMemo(
    () => buildProfile(mode, learnChoice, contributeChoice, featureText),
    [mode, learnChoice, contributeChoice, featureText],
  );
  const repoReady = store.repoStatus?.status === "ready" || store.repoStatus?.status === "stale";
  const repoError = store.repoStatus?.status === "error";
  const progress = store.repoStatus?.progress ?? (repoId ? 5 : 0);
  const repoDisplayName = repositoryName(repoUrl);

  useEffect(() => {
    void api.getAccountUsage().then(setUsage).catch(() => {
      setErrorMessage("Could not load the free usage allowance.");
    });
  }, []);

  useEffect(() => {
    if (tourId && repoId) return;
    const params = new URLSearchParams(window.location.search);
    const routeTourId = params.get("tour");
    const routeRepoId = params.get("repo");
    if (!routeTourId || !routeRepoId) return;
    setTourId(routeTourId);
    setRepoId(routeRepoId);
    setStage("tour");
  }, [repoId, tourId]);

  useEffect(() => {
    if (!repoId || stage !== "capture") return;
    const eventSource = new EventSource(api.firstImpressionUrl(repoId), { withCredentials: true });
    const onMessage = (event: MessageEvent<string>) => {
      const parsed = JSON.parse(event.data) as TourEvent;
      setStore((current) => applyTourEvent(current, parsed, repoId));
    };
    eventSource.addEventListener("first_impression", onMessage as EventListener);
    eventSource.addEventListener("done", () => eventSource.close());
    eventSource.addEventListener("error", () => eventSource.close());
    return () => eventSource.close();
  }, [repoId, stage]);

  useEffect(() => {
    if (!repoId || stage !== "capture" || repoReady || repoError) return;
    const timeout = window.setTimeout(async () => {
      try {
        const status = await api.getRepoStatus(repoId);
        setStore((current) => applyRepoStatus(current, status));
        forcePoll();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "Could not refresh indexing status.");
      }
    }, 1500);
    return () => window.clearTimeout(timeout);
  }, [repoError, repoId, repoReady, pollTick, stage]);

  useEffect(() => {
    if (!tourId || !repoId || stage !== "tour") return;
    const controller = new AbortController();
    let active = true;

    const consumeTourStream = async () => {
      try {
        const response = await fetch(api.tourStreamUrl(tourId), {
          cache: "no-store",
          credentials: "include",
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(await response.text());
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Tour stream did not return a readable response.");

        const decoder = new TextDecoder();
        let buffer = "";
        while (active) {
          const result = await reader.read();
          if (result.done) break;
          buffer += decoder.decode(result.value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";
          for (const part of parts) {
            for (const tourEvent of parseSseFrame(`${part}\n\n`)) {
              if (active) {
                setStore((current) => applyTourEvent(current, tourEvent, repoId));
              }
            }
          }
        }
      } catch (error) {
        if (active && !controller.signal.aborted) {
          setErrorMessage(error instanceof Error ? error.message : "Unable to stream the tour.");
        }
      }
    };

    void consumeTourStream();
    return () => {
      active = false;
      controller.abort();
    };
  }, [repoId, stage, tourId]);

  useEffect(() => {
    const chunkId = store.viewer.chunkId;
    if (!chunkId || store.viewer.content) return;
    let active = true;
    setViewerLoading(true);
    void api
      .getChunk(chunkId)
      .then((chunk) => {
        if (active) setStore((current) => hydrateViewer(current, chunk));
      })
      .catch((error: unknown) => {
        if (active) {
          setErrorMessage(error instanceof Error ? error.message : "Could not open this source reference.");
        }
      })
      .finally(() => {
        if (active) setViewerLoading(false);
      });
    return () => {
      active = false;
    };
  }, [store.viewer.chunkId, store.viewer.content]);

  const submitRepo = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    if (!validPublicGithubUrl(repoUrl)) {
      setErrorMessage("Enter a public GitHub repository URL in the form https://github.com/owner/repository.");
      return;
    }
    setBusy(true);
    setErrorMessage(null);
    setRepoId(undefined);
    setTourId(undefined);
    setStore(initialTourStoreState);
    try {
      const created = await api.createRepo(repoUrl.trim());
      setUsage(await api.getAccountUsage());
      setRepoId(created.repo_id);
      setStore((current) =>
        applyRepoStatus(current, {
          status: created.status,
          progress: created.status === "ready" ? 100 : 5,
        }),
      );
    } catch (error) {
      if (error instanceof ApiError && error.code === "PROVIDER_KEY_REQUIRED") {
        setProviderDialogOpen(true);
      }
      setErrorMessage(error instanceof Error ? error.message : "Unable to reach the RepoPilot API.");
    } finally {
      setBusy(false);
    }
  };

  const startTour = async () => {
    if (!repoId || !repoReady) return;
    setBusy(true);
    setErrorMessage(null);
    try {
      const created = await api.createTour(repoId, profile);
      setStore(initialTourStoreState);
      setTourId(created.tour_id);
      setStage("tour");
      router.push(`/?tour=${created.tour_id}&repo=${encodeURIComponent(repoId)}`);
    } catch (error) {
      setStage("capture");
      setErrorMessage(error instanceof Error ? error.message : "Unable to start the tour.");
    } finally {
      setBusy(false);
    }
  };

  const askAnything = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!tourId || !repoId || !askPrompt.trim() || asking) return;
    setAsking(true);
    setErrorMessage(null);
    try {
      const prompt = askPrompt.trim();
      const answer = await api.askTour(tourId, prompt);
      setUsage(await api.getAccountUsage());
      const claims: ClaimEvent[] = answer.claims.map((claim) => ({
        ...claim,
        event: "claim",
        v: 1,
      }));
      setStore((current) => appendAnswerAsSection(current, prompt, answer.answer, claims, repoId));
      const first = answer.claims[0];
      if (first) setStore((current) => selectClaim(current, first.id));
      setAskPrompt("");
    } catch (error) {
      if (error instanceof ApiError && error.code === "PROVIDER_KEY_REQUIRED") {
        setProviderDialogOpen(true);
      }
      setErrorMessage(error instanceof Error ? error.message : "Unable to query this snapshot.");
    } finally {
      setAsking(false);
    }
  };

  const viewerLines = useMemo(() => {
    if (!store.viewer.content || !store.viewer.startLine || !store.viewer.endLine) return [];
    return splitLines(store.viewer.content, store.viewer.startLine, store.viewer.endLine);
  }, [store.viewer.content, store.viewer.endLine, store.viewer.startLine]);

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

  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="product-brand" href="/" aria-label="RepoPilot home">
          <span className="brand-symbol" aria-hidden="true">
            <GitBranch size={19} weight="bold" />
          </span>
          <span>RepoPilot</span>
        </a>
        <button className="usage-control" type="button" onClick={() => setProviderDialogOpen(true)}>
          <LockKey size={17} weight={usage?.provider_connected ? "fill" : "regular"} aria-hidden="true" />
          <span>
            {usage?.provider_connected
              ? "Your provider is connected"
              : `${usage?.free_questions_remaining ?? 5} free questions`}
          </span>
        </button>
      </header>

      {stage === "capture" ? (
        <div className="onboarding-layout">
          <section className="onboarding-intro" aria-labelledby="onboarding-title">
            <div>
              <p className="section-kicker">Repository onboarding</p>
              <h1 id="onboarding-title">Understand the code before you change it.</h1>
              <p className="intro-copy">
                Build a guided code-reading path grounded in the repository&apos;s actual files and symbols.
              </p>
            </div>

            <div className="product-principles" aria-label="How RepoPilot works">
              <div className="principle-row">
                <MagnifyingGlass size={21} aria-hidden="true" />
                <div>
                  <strong>Repository-specific retrieval</strong>
                  <span>Answers stay scoped to the indexed snapshot.</span>
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
                <FileCode size={21} aria-hidden="true" />
                <div>
                  <strong>Synchronized code reading</strong>
                  <span>Select a claim to inspect the supporting code immediately.</span>
                </div>
              </div>
            </div>

            <p className="scope-note">
              Supports Python, TypeScript, JavaScript, Java, Go, Rust, C-family languages, Ruby, PHP,
              Swift, Scala, Vue, Svelte, Kotlin, and shell repositories.
            </p>
          </section>

          <section className="setup-panel" aria-label="Configure repository tour">
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

            <form className="repo-form" onSubmit={submitRepo} noValidate>
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
                <button className="button button-primary repo-submit" type="submit" disabled={busy}>
                  {busy ? "Starting" : "Analyze"}
                  {!busy ? <ArrowRight size={17} weight="bold" aria-hidden="true" /> : null}
                </button>
              </div>
              <p id="repo-help" className="field-help">
                RepoPilot indexes the current default branch. Private repositories are not supported.
              </p>
            </form>

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
                    (repoReady
                      ? "The repository snapshot is ready. Choose your goal to begin."
                      : "Cloning files, creating chunks, and building the repository graph.")}
                </p>
              </div>
            ) : null}

            <div className="setup-divider" />

            <div className="setup-heading goal-heading">
              <div>
                <span className="step-label">Goal</span>
                <h2>What do you need?</h2>
              </div>
            </div>

            <div className="mode-switch" role="group" aria-label="Tour goal">
              <button
                type="button"
                className="mode-button"
                data-active={mode === "learn"}
                aria-pressed={mode === "learn"}
                onClick={() => setMode("learn")}
              >
                <BookOpenText size={18} aria-hidden="true" />
                Learn the codebase
              </button>
              <button
                type="button"
                className="mode-button"
                data-active={mode === "contribute"}
                aria-pressed={mode === "contribute"}
                onClick={() => setMode("contribute")}
              >
                <Wrench size={18} aria-hidden="true" />
                Plan a contribution
              </button>
            </div>

            <div className="goal-options">
              {(mode === "learn" ? learnChoices : contributeChoices).map((choice) => {
                const active =
                  mode === "learn"
                    ? learnChoice === choice.value
                    : contributeChoice === choice.value;
                return (
                  <button
                    key={choice.value}
                    type="button"
                    className="goal-option"
                    data-active={active}
                    aria-pressed={active}
                    onClick={() => {
                      if (mode === "learn") setLearnChoice(choice.value as LearnChoice);
                      else setContributeChoice(choice.value as ContributeChoice);
                    }}
                  >
                    <span className="option-check" aria-hidden="true">
                      {active ? <CheckCircle size={19} weight="fill" /> : null}
                    </span>
                    <span>
                      <strong>{choice.label}</strong>
                      <small>{choice.description}</small>
                    </span>
                  </button>
                );
              })}
            </div>

            {mode === "learn" && learnChoice === "specific feature" ? (
              <div className="feature-field">
                <label htmlFor="feature-focus">Feature or workflow</label>
                <input
                  id="feature-focus"
                  className="text-input"
                  value={featureText}
                  onChange={(event) => setFeatureText(event.target.value)}
                  placeholder="Authentication, routing, CLI, configuration"
                />
              </div>
            ) : null}

            {errorMessage ? (
              <div className="inline-alert" role="alert">
                <WarningCircle size={19} weight="fill" aria-hidden="true" />
                <span>{errorMessage}</span>
              </div>
            ) : null}

            <div className="setup-footer">
              <div className="intent-summary">
                <span>Tour focus</span>
                <strong>{profile.raw_text}</strong>
              </div>
              <button
                className="button button-primary start-button"
                type="button"
                onClick={startTour}
                disabled={!repoReady || busy}
              >
                {busy && repoReady ? "Building tour" : repoReady ? "Open guided tour" : "Waiting for snapshot"}
                {repoReady && !busy ? <ArrowRight size={17} weight="bold" aria-hidden="true" /> : null}
              </button>
            </div>
          </section>
        </div>
      ) : (
        <div className="workspace">
          <header className="workspace-header">
            <div className="workspace-title">
              <button
                className="icon-button"
                type="button"
                onClick={() => setStage("capture")}
                aria-label="Back to repository setup"
              >
                <ArrowLeft size={19} />
              </button>
              <div>
                <span>{repoDisplayName}</span>
                <h1>Guided repository tour</h1>
              </div>
            </div>
            <div className="workspace-meta">
              <span className="repo-status repo-status-ready">
                <CheckCircle size={16} weight="fill" aria-hidden="true" />
                Snapshot ready
              </span>
              <span className="focus-summary">{profile.raw_text}</span>
            </div>
          </header>

          {errorMessage || store.error ? (
            <div className="workspace-alert inline-alert" role="alert">
              <WarningCircle size={19} weight="fill" aria-hidden="true" />
              <span>{errorMessage || store.error}</span>
            </div>
          ) : null}

          <div className="workspace-grid">
            <aside className="tour-navigation" aria-label="Tour sections">
              <div className="navigation-heading">
                <ListBullets size={18} aria-hidden="true" />
                <span>Tour contents</span>
              </div>
              <nav>
                {store.sections.length > 0 ? (
                  store.sections.map((section) => (
                    <a key={section.order} href={`#section-${section.order}`}>
                      <span>{section.title}</span>
                      {section.done ? (
                        <CheckCircle size={16} weight="fill" aria-label="Complete" />
                      ) : (
                        <CaretRight size={15} aria-hidden="true" />
                      )}
                    </a>
                  ))
                ) : (
                  <div className="navigation-empty">Preparing the first section.</div>
                )}
              </nav>
              <div className="navigation-focus">
                <span>Focus keywords</span>
                <div className="keyword-list">
                  {(profile.focus_keywords ?? []).map((keyword) => (
                    <span key={keyword}>{keyword}</span>
                  ))}
                </div>
              </div>
            </aside>

            <section className="tour-content" aria-label="Guided tour" aria-live="polite">
              {store.sections.length === 0 ? (
                <div className="tour-loading" aria-label="Building guided tour">
                  <div className="skeleton skeleton-heading" />
                  <div className="skeleton skeleton-copy" />
                  <div className="skeleton skeleton-copy skeleton-copy-short" />
                  <div className="skeleton skeleton-claim" />
                </div>
              ) : (
                store.sections.map((section) => (
                  <article className="tour-section" id={`section-${section.order}`} key={section.order}>
                    <div className="tour-section-heading">
                      <h2>{section.title}</h2>
                      {section.done ? (
                        <span className="section-complete">
                          <CheckCircle size={16} weight="fill" aria-hidden="true" />
                          Complete
                        </span>
                      ) : (
                        <span className="section-streaming">Writing section</span>
                      )}
                    </div>
                    <p className="section-body">{section.body || "Generating a repository-grounded explanation."}</p>

                    {section.mermaid ? (
                      <div className="diagram-source">
                        <span>Architecture diagram source</span>
                        <pre>{section.mermaid}</pre>
                      </div>
                    ) : null}

                    {section.claimIds.length > 0 ? (
                      <div className="claim-group" aria-label={`Sources for ${section.title}`}>
                        <div className="claim-group-label">Verified sources</div>
                        {section.claimIds.map((claimId) => {
                          const claim = store.claimsById[claimId];
                          const flagged = claim.status === "flagged" || claim.status === "rejected";
                          return (
                            <button
                              key={claimId}
                              type="button"
                              className="claim-row"
                              data-active={store.selectedClaimId === claimId}
                              data-flagged={flagged}
                              onClick={() => setStore((current) => selectClaim(current, claimId))}
                            >
                              <span className="claim-icon" aria-hidden="true">
                                {flagged ? (
                                  <WarningCircle size={19} weight="fill" />
                                ) : (
                                  <ShieldCheck size={19} weight="fill" />
                                )}
                              </span>
                              <span className="claim-content">
                                <strong>{claim.text}</strong>
                                <span className="claim-reference">
                                  {claim.refs[0].file_path}:{claim.refs[0].start_line}-{claim.refs[0].end_line}
                                </span>
                                {claim.verifier_note ? <small>{claim.verifier_note}</small> : null}
                              </span>
                              <span className={claimBadgeClass(claim.status)}>
                                {flagged ? "Review" : "Verified"}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    ) : null}
                  </article>
                ))
              )}

              <form className="ask-panel" onSubmit={askAnything}>
                <div className="ask-heading">
                  <label htmlFor="ask-repository">Ask this repository</label>
                  <button type="button" onClick={() => setProviderDialogOpen(true)}>
                    <LockKey size={15} aria-hidden="true" />
                    {usage?.provider_connected
                      ? "Using your provider"
                      : `${usage?.free_questions_remaining ?? 5} free remaining`}
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
                <p>Answers use only the indexed snapshot and include source references.</p>
              </form>
            </section>

            <aside className="code-inspector" aria-label="Synchronized Code Viewer">
              <div className="code-inspector-header">
                <div className="file-heading">
                  <FileCode size={19} aria-hidden="true" />
                  <div>
                    <span>Synchronized Code Viewer</span>
                    <strong>{store.viewer.filePath ?? "Select a verified source"}</strong>
                  </div>
                </div>
                {store.viewer.startLine ? (
                  <span className="line-range">
                    L{store.viewer.startLine}-L{store.viewer.endLine}
                  </span>
                ) : null}
              </div>

              {store.viewer.summary ? <p className="code-summary">{store.viewer.summary}</p> : null}

              <div className="code-frame" data-empty={viewerLines.length === 0}>
                {viewerLoading ? (
                  <div className="code-loading">
                    <div className="skeleton skeleton-code" />
                    <div className="skeleton skeleton-code skeleton-code-short" />
                    <div className="skeleton skeleton-code" />
                  </div>
                ) : viewerLines.length > 0 ? (
                  <pre>
                    {viewerLines.map((line, index) => (
                      <span className={line.active ? "code-line code-line-active" : "code-line"} key={`${line.number}-${index}`}>
                        <span className="line-number">{line.number}</span>
                        <span className="line-content">{line.content || " "}</span>
                      </span>
                    ))}
                  </pre>
                ) : (
                  <div className="code-empty">
                    <FileCode size={28} aria-hidden="true" />
                    <strong>No source selected</strong>
                    <span>Choose a verified claim to inspect its supporting code.</span>
                  </div>
                )}
              </div>
            </aside>
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

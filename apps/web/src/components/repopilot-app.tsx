"use client";

import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  api,
  type ClaimEvent,
  type ClaimStatus,
  type IntentProfile,
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
type ContributeChoice = "fix a reported issue" | "improve code quality" | "hunt for likely problems" | "show all, ranked";
type Mode = "learn" | "contribute";

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
    if (!eventName || dataLines.length === 0) {
      continue;
    }
    events.push(JSON.parse(dataLines.join("\n")) as TourEvent);
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

function splitLines(content: string, startLine: number, endLine: number): string[] {
  const lines = content.split("\n");
  return lines.map((line, index) => {
    const lineNumber = index + startLine;
    const active = lineNumber >= startLine && lineNumber <= endLine;
    return `${active ? ">>" : "  "} ${lineNumber.toString().padStart(4, " ")} ${line}`;
  });
}

function badgeClass(status: ClaimStatus): string {
  return status === "flagged" ? "badge badge-flagged" : "badge badge-verified";
}

export default function RepoPilotApp() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/flask");
  const [repoId, setRepoId] = useState<string>();
  const [tourId, setTourId] = useState<string>();
  const [mode, setMode] = useState<Mode>("learn");
  const [learnChoice, setLearnChoice] = useState<LearnChoice>("overall structure");
  const [contributeChoice, setContributeChoice] = useState<ContributeChoice>("improve code quality");
  const [featureText, setFeatureText] = useState("");
  const [askPrompt, setAskPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [stage, setStage] = useState<"capture" | "tour">("capture");
  const [store, setStore] = useState<TourStoreState>(initialTourStoreState);
  const [pollTick, forcePoll] = useReducer((value: number) => value + 1, 0);
  const impressionRef = useRef<EventSource | null>(null);

  const profile = useMemo(
    () => buildProfile(mode, learnChoice, contributeChoice, featureText),
    [mode, learnChoice, contributeChoice, featureText],
  );

  useEffect(() => {
    if (!repoId || stage !== "capture") {
      return;
    }
    const eventSource = new EventSource(api.firstImpressionUrl(repoId));
    impressionRef.current = eventSource;
    const onMessage = (event: MessageEvent<string>) => {
      const parsed = JSON.parse(event.data) as TourEvent;
      setStore((current) => applyTourEvent(current, parsed, repoId));
    };
    eventSource.addEventListener("first_impression", onMessage as EventListener);
    eventSource.addEventListener("done", () => eventSource.close());
    return () => eventSource.close();
  }, [repoId, stage]);

  useEffect(() => {
    if (!repoId || stage !== "capture") {
      return;
    }
    const timeout = window.setTimeout(async () => {
      try {
        const status = await api.getRepoStatus(repoId);
        setStore((current) => applyRepoStatus(current, status));
        forcePoll();
      } catch {
        window.clearTimeout(timeout);
      }
    }, store.repoStatus?.status === "ready" ? 8000 : 1500);
    return () => window.clearTimeout(timeout);
  }, [repoId, stage, pollTick, store.repoStatus?.status]);

  const submitRepo = async () => {
    setBusy(true);
    setErrorMessage(null);
    try {
      const created = await api.createRepo(repoUrl);
      setRepoId(created.repo_id);
      setStore((current) =>
        applyRepoStatus(
          {
            ...current,
            firstImpression: "",
          },
          { status: created.status, progress: 5 },
        ),
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to reach the API.");
    } finally {
      setBusy(false);
    }
  };

  const startTour = async () => {
    if (!repoId) {
      return;
    }
    setBusy(true);
    setErrorMessage(null);
    try {
      const created = await api.createTour(repoId, profile);
      setTourId(created.tour_id);
      setStage("tour");
      router.push(`/?tour=${created.tour_id}&repo=${encodeURIComponent(repoId)}`);
      const response = await fetch(api.tourStreamUrl(created.tour_id), { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error("Tour stream did not return a readable response.");
      }
      let buffer = "";
      while (true) {
        const result = await reader.read();
        if (result.done) {
          break;
        }
        buffer += decoder.decode(result.value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          for (const event of parseSseFrame(`${part}\n\n`)) {
            setStore((current) => applyTourEvent(current, event, repoId));
          }
        }
      }
    } catch (error) {
      setStage("capture");
      setErrorMessage(error instanceof Error ? error.message : "Unable to start the tour.");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    const chunkId = store.viewer.chunkId;
    if (!chunkId || store.viewer.content) {
      return;
    }
    void api.getChunk(chunkId).then((chunk) => {
      setStore((current) => hydrateViewer(current, chunk));
    });
  }, [store.viewer.chunkId, store.viewer.content]);

  const askAnything = async () => {
    if (!tourId || !repoId || !askPrompt.trim()) {
      return;
    }
    setErrorMessage(null);
    try {
      const answer = await api.askTour(tourId, askPrompt.trim());
      const claims: ClaimEvent[] = answer.claims.map((claim) => ({
        ...claim,
        event: "claim",
        v: 1,
      }));
      setStore((current) => appendAnswerAsSection(current, askPrompt.trim(), answer.answer, claims, repoId));
      const first = answer.claims[0];
      if (first) {
        setStore((current) => selectClaim(current, first.id));
      }
      setAskPrompt("");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to ask the snapshot right now.");
    }
  };

  const viewerLines = useMemo(() => {
    if (!store.viewer.content || !store.viewer.startLine || !store.viewer.endLine) {
      return [];
    }
    return splitLines(store.viewer.content, store.viewer.startLine, store.viewer.endLine);
  }, [store.viewer.content, store.viewer.endLine, store.viewer.startLine]);

  return (
    <main className="shell">
      <div className="topbar">
        <div className="brand-mark">Phase 4 • Experience</div>
        <div className="timeline-chip">
          <span>API + Web</span>
          <span className="muted">Live repo onboarding with synchronized code reading</span>
        </div>
      </div>

      {stage === "capture" ? (
        <section className="hero">
          <div className="hero-panel hero-left">
            <div className="brand-copy">
              <p className="eyebrow">Grounded Repo Tours</p>
              <h1>Paste a repo and get a code-reading path before indexing is even done.</h1>
              <p className="hero-sub">
                RepoPilot starts the structural snapshot in the background, captures why you are here
                immediately, and turns the first useful signals into a guided tour with clickable code refs.
              </p>
            </div>

            <div className="hero-grid">
              <div className="micro-card">
                <strong>Parallel Start</strong>
                <span>Indexing runs while you choose how you want the repo framed.</span>
              </div>
              <div className="micro-card">
                <strong>Grounded Claims</strong>
                <span>Every claim is attached to a concrete file span ready for the code viewer.</span>
              </div>
              <div className="micro-card">
                <strong>First Impression</strong>
                <span>Before the full tour lands, you still get a structural read on the snapshot.</span>
              </div>
              <div className="micro-card">
                <strong>Ask Anything</strong>
                <span>Free-form Q&A opens the code viewer to the first grounded answer ref.</span>
              </div>
            </div>
          </div>

          <div className="hero-panel hero-right">
            <div>
              <label className="input-label" htmlFor="repo-url">
                Repo URL
              </label>
              <div className="repo-form">
                <input
                  id="repo-url"
                  className="repo-input"
                  value={repoUrl}
                  onChange={(event) => setRepoUrl(event.target.value)}
                  placeholder="https://github.com/pallets/flask"
                />
                <div className="button-row">
                  <button className="primary-button" onClick={submitRepo} disabled={busy}>
                    {busy ? "Starting…" : "Index And Continue"}
                  </button>
                  {repoId ? (
                    <button className="secondary-button" onClick={() => forcePoll()}>
                      Refresh Status
                    </button>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="panel" style={{ padding: 0, background: "transparent", boxShadow: "none" }}>
              <div style={{ padding: "0 0 12px" }}>
                <p className="eyebrow">Why Are You Here?</p>
              </div>
              <div className="choice-grid">
                <button
                  className="choice-button"
                  data-active={mode === "learn"}
                  onClick={() => setMode("learn")}
                >
                  <strong className="choice-title">I want to learn this codebase</strong>
                  <span className="choice-copy">
                    Frame the tour around entry points, system shape, and a code-reading path.
                  </span>
                </button>
                <button
                  className="choice-button"
                  data-active={mode === "contribute"}
                  onClick={() => setMode("contribute")}
                >
                  <strong className="choice-title">I want to contribute to it</strong>
                  <span className="choice-copy">
                    Bias the tour toward quality hotspots, risk zones, and where edits will compound.
                  </span>
                </button>
              </div>
            </div>

            {mode === "learn" ? (
              <div>
                <p className="input-label">What part interests you most?</p>
                <div className="chip-strip">
                  {(["overall structure", "specific feature", "data model"] as LearnChoice[]).map((choice) => (
                    <button
                      key={choice}
                      className="chip-button"
                      data-active={learnChoice === choice}
                      onClick={() => setLearnChoice(choice)}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
                {learnChoice === "specific feature" ? (
                  <div style={{ marginTop: 12 }}>
                    <input
                      className="freeform-input"
                      value={featureText}
                      onChange={(event) => setFeatureText(event.target.value)}
                      placeholder="Authentication, routing, CLI, config loading…"
                    />
                  </div>
                ) : null}
              </div>
            ) : (
              <div>
                <p className="input-label">What kind of contribution?</p>
                <div className="chip-strip">
                  {(
                    [
                      "fix a reported issue",
                      "improve code quality",
                      "hunt for likely problems",
                      "show all, ranked",
                    ] as ContributeChoice[]
                  ).map((choice) => (
                    <button
                      key={choice}
                      className="chip-button"
                      data-active={contributeChoice === choice}
                      onClick={() => setContributeChoice(choice)}
                    >
                      {choice}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="first-impression" aria-live="polite">
              <strong className="choice-title">First Impression</strong>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${store.repoStatus?.progress ?? 4}%` }}
                />
              </div>
              <p className="progress-copy">
                {store.firstImpression ||
                  "Once the first structural signals land, this panel will summarize the snapshot while indexing continues."}
              </p>
              <p className="meta-copy">
                Status: {store.repoStatus?.status ?? "waiting"}{" "}
                {store.repoStatus?.status === "stale"
                  ? "• cached index available, re-index recommended"
                  : null}
              </p>
              {errorMessage ? (
                <p className="meta-copy" style={{ color: "#ff8b8b", marginTop: 12 }}>
                  {errorMessage}
                </p>
              ) : null}
            </div>

            <div className="button-row">
              <button
                className="primary-button"
                onClick={startTour}
                disabled={!repoId || store.repoStatus?.status === "error" || busy}
              >
                Start Tour
              </button>
              <div className="timeline-chip">
                <span>You said:</span>
                <span className="muted">{profile.raw_text}</span>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="tour-shell">
          <div className="tour-column">
            <div className="panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Tour View</p>
                  <h2 style={{ marginBottom: 8 }}>You said: {profile.raw_text}</h2>
                  <p className="muted">
                    {store.repoStatus?.status === "ready"
                      ? "Indexed snapshot is ready."
                      : "Tour stream will keep filling in as the API emits sections."}
                  </p>
                </div>
                <button className="inline-link" onClick={() => setStage("capture")}>
                  change
                </button>
              </div>

              {store.repoStatus && store.repoStatus.status !== "ready" ? (
                <div style={{ marginBottom: 18 }}>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${store.repoStatus.progress ?? 18}%` }}
                    />
                  </div>
                </div>
              ) : null}

              <div className="tour-stream" aria-live="polite">
                {store.sections.map((section) => (
                  <article className="section-card" key={section.order}>
                    <h3>{section.title}</h3>
                    <p className="muted">{section.body || "Streaming section copy…"}</p>
                    {section.mermaid ? (
                      <div className="mermaid-block">
                        <pre style={{ margin: 0 }}>{section.mermaid}</pre>
                      </div>
                    ) : null}
                    <div className="claim-list">
                      {section.claimIds.map((claimId) => {
                        const claim = store.claimsById[claimId];
                        return (
                          <button
                            key={claimId}
                            className="claim-button"
                            data-active={store.selectedClaimId === claimId}
                            onClick={() => setStore((current) => selectClaim(current, claimId))}
                          >
                            <div>{claim.text}</div>
                            <div className="claim-meta">
                              <span className={badgeClass(claim.status)}>
                                {claim.status === "flagged" ? "Flagged" : "Grounded"}
                              </span>
                              <span className="badge badge-path">
                                {claim.retrieval_path.join(" → ")}
                              </span>
                              {claim.verifier_note ? <span>{claim.verifier_note}</span> : null}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div className="panel">
              <p className="eyebrow">Ask Anything</p>
              {errorMessage ? (
                <p className="meta-copy" style={{ color: "#ff8b8b", marginBottom: 12 }}>
                  {errorMessage}
                </p>
              ) : null}
              <div className="ask-form">
                <input
                  className="ask-input"
                  value={askPrompt}
                  onChange={(event) => setAskPrompt(event.target.value)}
                  placeholder="Where should I start if I care about routing?"
                />
                <div className="button-row">
                  <button className="primary-button" onClick={askAnything}>
                    Ask The Snapshot
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="code-column">
            <div className="panel code-panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">Synchronized Code Viewer</p>
                  <h3 style={{ marginBottom: 6 }}>{store.viewer.filePath ?? "Select a claim"}</h3>
                  <p className="muted">
                    {store.viewer.summary ?? "Click any grounded claim and the matching chunk will open here."}
                  </p>
                </div>
              </div>

              <div className="code-frame">
                <pre>
                  {viewerLines.length > 0
                    ? viewerLines.map((line) => (
                        <span
                          key={line}
                          className={line.startsWith(">>") ? "line-highlight" : undefined}
                        >
                          {line}
                        </span>
                      ))
                    : "No code selected yet."}
                </pre>
              </div>
            </div>

            <div className="panel">
              <p className="eyebrow">Intent Focus</p>
              <div className="chip-strip">
                {(profile.focus_keywords ?? []).map((keyword) => (
                  <span key={keyword} className="timeline-chip">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

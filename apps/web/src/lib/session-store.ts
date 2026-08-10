import type {
  ClaimPayload,
  CodeRef,
  FirstImpressionEvent,
  IntentProfile,
  RepoStatusResponse,
  TourMessage,
} from "./api/generated.ts";

export interface StoredClaim extends ClaimPayload {
  chunkId: string;
}

/** One question and the answer it produced, in the order they were asked. */
export interface Exchange {
  id: number;
  question: string;
  answer: string;
  claimIds: string[];
  /** The persona in force when this question was asked. */
  personaLabel: string;
}

export interface SessionState {
  repoStatus?: RepoStatusResponse;
  firstImpression: string;
  exchanges: Exchange[];
  claimsById: Record<string, StoredClaim>;
  selectedClaimId?: string;
  error?: string;
}

export const initialSessionState: SessionState = {
  firstImpression: "",
  exchanges: [],
  claimsById: {},
};

export function encodeChunkId(repoId: string, ref: CodeRef): string {
  const payload = JSON.stringify({
    repo_id: repoId,
    file_path: ref.file_path,
    start_line: ref.start_line,
    end_line: ref.end_line,
    symbol: ref.symbol ?? null,
  });
  if (typeof window === "undefined") {
    return Buffer.from(payload, "utf-8").toString("base64url");
  }
  return window.btoa(payload).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Record an answered question, indexing its claims and focusing the first one. */
export function appendExchange(
  state: SessionState,
  input: {
    question: string;
    answer: string;
    claims: ClaimPayload[];
    personaLabel: string;
    repoId: string;
  },
): SessionState {
  const claimsById = { ...state.claimsById };
  const claimIds: string[] = [];
  for (const claim of input.claims) {
    const ref = claim.refs[0];
    if (!ref) continue;
    claimsById[claim.id] = { ...claim, chunkId: encodeChunkId(input.repoId, ref) };
    claimIds.push(claim.id);
  }

  const exchange: Exchange = {
    id: state.exchanges.length,
    question: input.question,
    answer: input.answer,
    claimIds,
    personaLabel: input.personaLabel,
  };

  const next: SessionState = {
    ...state,
    exchanges: [...state.exchanges, exchange],
    claimsById,
    error: undefined,
  };

  // Focus the newest answer's first source, so the reader lands on evidence
  // rather than on whatever they last clicked.
  const firstClaimId = claimIds[0];
  return firstClaimId ? selectClaim(next, firstClaimId) : next;
}

/** Replay a persisted tour's exchanges into a fresh session state. */
export function hydrateFromTour(
  tour: { repo_id: string; messages: TourMessage[] },
  firstImpression = "",
): SessionState {
  return tour.messages.reduce<SessionState>(
    (state, message) =>
      appendExchange(state, {
        question: message.question,
        answer: message.answer,
        claims: message.claims,
        personaLabel: message.persona_label,
        repoId: tour.repo_id,
      }),
    { ...initialSessionState, firstImpression },
  );
}

export function selectClaim(state: SessionState, claimId: string): SessionState {
  if (!state.claimsById[claimId]) {
    return state;
  }
  return { ...state, selectedClaimId: claimId };
}

export function applyFirstImpression(
  state: SessionState,
  event: FirstImpressionEvent,
): SessionState {
  return { ...state, firstImpression: event.text };
}

export function applyRepoStatus(state: SessionState, status: RepoStatusResponse): SessionState {
  return { ...state, repoStatus: status };
}

/** Name a chat after the question that opened it, the way ChatGPT does. */
export function chatTitle(question: string): string {
  const cleaned = question.trim().replace(/\s+/g, " ").replace(/[?.!,;:]+$/, "");
  return cleaned.length > 48 ? `${cleaned.slice(0, 48).trimEnd()}…` : cleaned;
}

/** Short human label for a profile, shown against each answer. */
export function personaLabel(profile: IntentProfile | null): string {
  if (!profile) return "No lens";
  return profile.audience_framing?.trim() || profile.raw_text;
}

import type {
  ChunkPayload,
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

export interface ViewerState {
  chunkId?: string;
  filePath?: string;
  startLine?: number;
  endLine?: number;
  content?: string;
  summary?: string | null;
}

export interface SessionState {
  repoStatus?: RepoStatusResponse;
  firstImpression: string;
  exchanges: Exchange[];
  claimsById: Record<string, StoredClaim>;
  selectedClaimId?: string;
  viewer: ViewerState;
  error?: string;
}

export const initialSessionState: SessionState = {
  firstImpression: "",
  exchanges: [],
  claimsById: {},
  viewer: {},
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

  // Jump the code viewer to the newest answer's first source, so the reader
  // lands on evidence rather than on whatever they last clicked.
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
  const claim = state.claimsById[claimId];
  if (!claim) {
    return state;
  }
  const ref = claim.refs[0];
  return {
    ...state,
    selectedClaimId: claimId,
    viewer: {
      chunkId: claim.chunkId,
      filePath: ref.file_path,
      startLine: ref.start_line,
      endLine: ref.end_line,
      content: undefined,
      summary: undefined,
    },
  };
}

export function hydrateViewer(state: SessionState, chunk: ChunkPayload): SessionState {
  return {
    ...state,
    viewer: {
      chunkId: chunk.chunk_id,
      filePath: chunk.ref.file_path,
      startLine: chunk.ref.start_line,
      endLine: chunk.ref.end_line,
      content: chunk.content,
      summary: chunk.summary,
    },
  };
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

/** Short human label for a profile, shown against each answer. */
export function personaLabel(profile: IntentProfile | null): string {
  if (!profile) return "No lens";
  return profile.audience_framing?.trim() || profile.raw_text;
}

import type {
  ChunkPayload,
  ClaimEvent,
  CodeRef,
  FirstImpressionEvent,
  RepoStatusResponse,
  TourEvent,
} from "./api/generated.ts";

export interface StoredClaim extends ClaimEvent {
  chunkId: string;
}

export interface TourSection {
  order: number;
  title: string;
  body: string;
  claimIds: string[];
  mermaid?: string;
  done?: boolean;
}

export interface ViewerState {
  chunkId?: string;
  filePath?: string;
  startLine?: number;
  endLine?: number;
  content?: string;
  summary?: string | null;
}

export interface TourStoreState {
  repoStatus?: RepoStatusResponse;
  firstImpression: string;
  sections: TourSection[];
  claimsById: Record<string, StoredClaim>;
  selectedClaimId?: string;
  viewer: ViewerState;
  streamDone: boolean;
  error?: string;
}

export const initialTourStoreState: TourStoreState = {
  firstImpression: "",
  sections: [],
  claimsById: {},
  viewer: {},
  streamDone: false,
};

function nextSection(state: TourStoreState, order: number, title: string): TourSection[] {
  const filtered = state.sections.filter((section) => section.order !== order);
  return [...filtered, { order, title, body: "", claimIds: [] }].sort((a, b) => a.order - b.order);
}

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

export function applyTourEvent(
  state: TourStoreState,
  event: TourEvent,
  repoId: string,
): TourStoreState {
  if (event.event === "section_start") {
    return {
      ...state,
      sections: nextSection(state, event.order, event.title),
    };
  }

  if (event.event === "token") {
    const sections = [...state.sections];
    const last = sections[sections.length - 1];
    if (last) {
      sections[sections.length - 1] = { ...last, body: `${last.body}${event.text}` };
    }
    return { ...state, sections };
  }

  if (event.event === "claim") {
    const chunkId = encodeChunkId(repoId, event.refs[0]);
    const storedClaim: StoredClaim = { ...event, chunkId };
    const sections = [...state.sections];
    const last = sections[sections.length - 1];
    if (last) {
      sections[sections.length - 1] = {
        ...last,
        claimIds: [...last.claimIds, event.id],
      };
    }
    return {
      ...state,
      sections,
      claimsById: {
        ...state.claimsById,
        [event.id]: storedClaim,
      },
      selectedClaimId: state.selectedClaimId ?? event.id,
      viewer:
        state.selectedClaimId == null
          ? {
              chunkId,
              filePath: event.refs[0].file_path,
              startLine: event.refs[0].start_line,
              endLine: event.refs[0].end_line,
            }
          : state.viewer,
    };
  }

  if (event.event === "diagram") {
    const sections = [...state.sections];
    const last = sections[sections.length - 1];
    if (last) {
      sections[sections.length - 1] = { ...last, mermaid: event.mermaid };
    }
    return { ...state, sections };
  }

  if (event.event === "section_end") {
    const sections = state.sections.map((section) =>
      section.order === event.order ? { ...section, done: true } : section,
    );
    return { ...state, sections };
  }

  if (event.event === "first_impression") {
    return { ...state, firstImpression: event.text };
  }

  if (event.event === "error") {
    return { ...state, error: event.message };
  }

  if (event.event === "done") {
    return { ...state, streamDone: true };
  }

  return state;
}

export function selectClaim(state: TourStoreState, claimId: string): TourStoreState {
  const claim = state.claimsById[claimId];
  if (!claim) {
    return state;
  }
  return {
    ...state,
    selectedClaimId: claimId,
    viewer: {
      ...state.viewer,
      chunkId: claim.chunkId,
      filePath: claim.refs[0].file_path,
      startLine: claim.refs[0].start_line,
      endLine: claim.refs[0].end_line,
    },
  };
}

export function hydrateViewer(state: TourStoreState, chunk: ChunkPayload): TourStoreState {
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
  state: TourStoreState,
  event: FirstImpressionEvent,
): TourStoreState {
  return { ...state, firstImpression: event.text };
}

export function applyRepoStatus(
  state: TourStoreState,
  status: RepoStatusResponse,
): TourStoreState {
  return { ...state, repoStatus: status };
}

export function appendAnswerAsSection(
  state: TourStoreState,
  prompt: string,
  answer: string,
  claims: ClaimEvent[],
  repoId: string,
): TourStoreState {
  let next = {
    ...state,
    sections: [
      ...state.sections,
      {
        order: state.sections.length,
        title: `Ask: ${prompt}`,
        body: answer,
        claimIds: [],
      },
    ],
  };
  for (const claim of claims) {
    next = applyTourEvent(next, claim, repoId);
  }
  return next;
}

export const storeTestHelpers = {
  nextSection,
};

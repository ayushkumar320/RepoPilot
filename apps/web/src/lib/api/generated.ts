export type RepoStatus = "queued" | "indexing" | "ready" | "error" | "stale";
export type ClaimStatus = "unverified" | "verified" | "rejected" | "flagged";

export interface CodeRef {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol?: string | null;
}

export interface IntentProfile {
  raw_text: string;
  modality_weights?: Partial<Record<"understand" | "change" | "evaluate" | "locate" | "compare", number>>;
  focus_keywords?: string[];
  audience_framing?: string | null;
  output_shape_preference?: "narrative" | "ranked_list" | "dossier" | "comparison_table" | "unspecified";
  success_criterion?: string | null;
}

export interface CreateRepoResponse {
  repo_id: string;
  status: RepoStatus;
}

export interface RepoStatusResponse {
  status: RepoStatus;
  progress?: number | null;
  error?: string | null;
  indexed_sha?: string | null;
  remote_sha?: string | null;
  commits_behind_estimate?: number | null;
}

export interface CreateTourResponse {
  tour_id: string;
  stream_url: string;
}

export interface TourClaimPayload {
  id: string;
  text: string;
  refs: CodeRef[];
  status: ClaimStatus;
  verifier_note?: string | null;
  retrieval_path: string[];
}

export interface QAAnswerResponse {
  answer: string;
  claims: TourClaimPayload[];
  retrieval_path: string[];
}

export interface ChunkPayload {
  chunk_id: string;
  repo_id: string;
  ref: CodeRef;
  content: string;
  summary?: string | null;
}

export interface SectionStartEvent {
  event: "section_start";
  v: 1;
  order: number;
  title: string;
}

export interface TokenEvent {
  event: "token";
  v: 1;
  text: string;
}

export interface ClaimEvent extends TourClaimPayload {
  event: "claim";
  v: 1;
}

export interface DiagramEvent {
  event: "diagram";
  v: 1;
  mermaid: string;
}

export interface SectionEndEvent {
  event: "section_end";
  v: 1;
  order: number;
}

export interface FirstImpressionEvent {
  event: "first_impression";
  v: 1;
  text: string;
}

export interface DoneEvent {
  event: "done";
  v: 1;
}

export interface ErrorEvent {
  event: "error";
  v: 1;
  code: string;
  message: string;
}

export type TourEvent =
  | SectionStartEvent
  | TokenEvent
  | ClaimEvent
  | DiagramEvent
  | SectionEndEvent
  | FirstImpressionEvent
  | DoneEvent
  | ErrorEvent;

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return (await response.json()) as T;
}

export const api = {
  createRepo(repoUrl: string): Promise<CreateRepoResponse> {
    return http("/repos", {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    });
  },
  getRepoStatus(repoId: string): Promise<RepoStatusResponse> {
    return http(`/repos/${repoId}/status`);
  },
  createTour(repoId: string, intentProfile: IntentProfile): Promise<CreateTourResponse> {
    return http("/tours", {
      method: "POST",
      body: JSON.stringify({ repo_id: repoId, intent_profile: intentProfile }),
    });
  },
  askTour(tourId: string, question: string): Promise<QAAnswerResponse> {
    return http(`/tours/${tourId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    });
  },
  getChunk(chunkId: string): Promise<ChunkPayload> {
    return http(`/chunks/${chunkId}`);
  },
  firstImpressionUrl(repoId: string): string {
    return `${API_BASE}/repos/${repoId}/first-impression`;
  },
  tourStreamUrl(tourId: string): string {
    return `${API_BASE}/tours/${tourId}/stream`;
  },
};

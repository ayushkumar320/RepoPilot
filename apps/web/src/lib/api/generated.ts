export type RepoStatus = "queued" | "indexing" | "ready" | "error" | "stale";

export interface AccountUsage {
  free_repositories_remaining: number;
  provider_connected: boolean;
  groq_connected: boolean;
  huggingface_connected: boolean;
  credential_storage: "session_only" | "account_bound";
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export type ClaimStatus = "unverified" | "verified" | "rejected" | "flagged";

export interface CodeRef {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol?: string | null;
}

export type OutputShape =
  | "narrative"
  | "ranked_list"
  | "dossier"
  | "comparison_table"
  | "unspecified";

export interface IntentProfile {
  raw_text: string;
  modality_weights?: Partial<Record<"understand" | "change" | "evaluate" | "locate" | "compare", number>>;
  focus_keywords?: string[];
  audience_framing?: string | null;
  output_shape_preference?: OutputShape;
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

export interface ClaimPayload {
  id: string;
  text: string;
  refs: CodeRef[];
  status: ClaimStatus;
  verifier_note?: string | null;
  retrieval_path: string[];
}

export interface QAAnswerResponse {
  answer: string;
  claims: ClaimPayload[];
  retrieval_path: string[];
}

export interface ChunkPayload {
  chunk_id: string;
  repo_id: string;
  ref: CodeRef;
  content: string;
  summary?: string | null;
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

export type RepoEvent = FirstImpressionEvent | DoneEvent | ErrorEvent;

export interface Identity {
  session_id: string;
  authenticated: boolean;
  provider?: string | null;
  provider_account_id?: string | null;
  display_name?: string | null;
  email?: string | null;
  avatar_url?: string | null;
}

export interface TourSummary {
  tour_id: string;
  repo_id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface TourMessage {
  ordinal: number;
  question: string;
  answer: string;
  claims: ClaimPayload[];
  persona_label: string;
}

export interface TourDetail extends TourSummary {
  snapshot_repo_id?: string | null;
  intent_profile?: IntentProfile | null;
  messages: TourMessage[];
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "/api";

const RETRYABLE_STATUS = new Set([500, 502, 503, 504]);

// Only idempotent requests may be auto-retried: reads (GET) and repo submission
// (POST /repos is idempotent on repo_url). We must NOT retry an /ask — it
// bills a provider call and appends to the transcript.
function isIdempotent(path: string, init?: RequestInit): boolean {
  const method = (init?.method ?? "GET").toUpperCase();
  return method === "GET" || path === "/repos";
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const send = (): Promise<Response> =>
    fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
      credentials: "include",
    });

  let response: Response;
  try {
    response = await send();
    // The Next.js dev proxy can surface a transient upstream connection reset
    // (ECONNRESET / socket hang up) as a 5xx; retry idempotent requests once.
    if (RETRYABLE_STATUS.has(response.status) && isIdempotent(path, init)) {
      response = await send();
    }
  } catch (error) {
    if (!isIdempotent(path, init)) throw error;
    response = await send();
  }

  if (!response.ok) {
    const text = await response.text();
    let message = text || `Request failed with status ${response.status}.`;
    let code: string | undefined;
    try {
      const payload = JSON.parse(text) as {
        detail?: string | { code?: string; message?: string };
      };
      if (typeof payload.detail === "string") message = payload.detail;
      if (typeof payload.detail === "object" && payload.detail) {
        message = payload.detail.message ?? message;
        code = payload.detail.code;
      }
    } catch {
      // Preserve the response body when an upstream proxy returns plain text.
    }
    throw new ApiError(message, response.status, code);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  getAccountUsage(): Promise<AccountUsage> {
    return http("/account/usage");
  },
  connectProvider(groqApiKey: string, huggingfaceApiKey?: string): Promise<AccountUsage> {
    return http("/account/provider", {
      method: "POST",
      body: JSON.stringify({
        groq_api_key: groqApiKey,
        huggingface_api_key: huggingfaceApiKey || null,
      }),
    });
  },
  disconnectProvider(): Promise<AccountUsage> {
    return http("/account/provider", { method: "DELETE" });
  },
  createRepo(repoUrl: string): Promise<CreateRepoResponse> {
    return http("/repos", {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    });
  },
  getRepoStatus(repoId: string): Promise<RepoStatusResponse> {
    return http(`/repos/${repoId}/status`);
  },
  // The persona travels with every question rather than being pinned to a
  // server-side record, so switching lenses mid-conversation costs nothing.
  askRepo(
    repoId: string,
    question: string,
    intentProfile: IntentProfile | null,
  ): Promise<QAAnswerResponse> {
    return http(`/repos/${repoId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question, intent_profile: intentProfile }),
    });
  },
  draftIntent(rawText: string): Promise<IntentProfile> {
    return http("/intent", {
      method: "POST",
      body: JSON.stringify({ raw_text: rawText }),
    });
  },
  getChunk(chunkId: string): Promise<ChunkPayload> {
    return http(`/chunks/${encodeURIComponent(chunkId)}`);
  },
  getIdentity(): Promise<Identity> {
    return http("/me");
  },
  saveIdentity(identity: {
    provider: string;
    provider_account_id: string;
    display_name?: string | null;
    email?: string | null;
    avatar_url?: string | null;
  }): Promise<Identity> {
    return http("/me", { method: "PUT", body: JSON.stringify(identity) });
  },
  createTour(
    repoId: string,
    intentProfile: IntentProfile | null,
    title?: string,
  ): Promise<{ tour_id: string }> {
    return http("/tours", {
      method: "POST",
      body: JSON.stringify({
        repo_id: repoId,
        intent_profile: intentProfile,
        title: title ?? null,
      }),
    });
  },
  listTours(): Promise<TourSummary[]> {
    return http("/tours");
  },
  getTour(tourId: string): Promise<TourDetail> {
    return http(`/tours/${encodeURIComponent(tourId)}`);
  },
  appendTourMessage(
    tourId: string,
    message: {
      question: string;
      answer: string;
      claims: ClaimPayload[];
      persona_label: string;
    },
  ): Promise<{ ordinal: number }> {
    return http(`/tours/${encodeURIComponent(tourId)}/messages`, {
      method: "POST",
      body: JSON.stringify(message),
    });
  },
  deleteTour(tourId: string): Promise<void> {
    return http(`/tours/${encodeURIComponent(tourId)}`, { method: "DELETE" });
  },
  firstImpressionUrl(repoId: string): string {
    return `${API_BASE}/repos/${repoId}/first-impression`;
  },
};

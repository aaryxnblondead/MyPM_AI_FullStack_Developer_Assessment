export type HealthStatus = {
  status: string;
};

export type EvidenceItem = {
  chunk_id: string;
  quote: string;
};

export type RequirementResult = {
  requirement_id: string;
  verdict: "met" | "partial" | "no_evidence";
  evidence: EvidenceItem[];
  reasoning: string;
  display?: string;
};

export type EvaluationCreate = {
  candidate_id?: string;
  job_description_id?: string;
  candidate_name?: string;
  target_role?: string;
  resume_text?: string;
  company_name?: string;
  job_title?: string;
  job_description?: string;
};

export type EvaluationRecord = {
  id: string;
  candidate_id: string;
  job_description_id: string;
  candidate_name: string;
  company_name: string;
  job_title: string;
  fit_category: string | null;
  fit_score: number | null;
  per_requirement: RequirementResult[] | null;
  explanation: string | null;
  explanation_edited: string | null;
  outreach_subject: string | null;
  outreach_subject_edited: string | null;
  outreach_body: string | null;
  outreach_body_edited: string | null;
  injection_flagged: boolean;
  injection_notes: string;
  resume_structured: ResumeStructured | null;
  created_at: string | null;
};

export type EvaluationListItem = {
  id: string;
  candidate_name: string;
  company_name: string;
  job_title: string;
  fit_category: string | null;
  fit_score: number | null;
  created_at: string | null;
};

export type ChunkItem = {
  id: string;
  chunk_index: number;
  section_label: string;
  text: string;
  char_start: number;
  char_end: number;
};

export type CandidateChunks = {
  candidate_id: string;
  name: string;
  resume_text: string;
  chunks: ChunkItem[];
};

export type CandidateDetail = {
  id: string;
  name: string;
  target_role: string;
  resume_structured: ResumeStructured | null;
  chunk_count: number;
  injection_flagged: boolean;
};

export type ResumeStructured = {
  skills: { name: string; source: string; known?: boolean }[];
  education: { detail: string; source: string }[];
  total_years_experience: number | null;
  roles: { title: string; company: string; bullets: string[]; source: string }[];
  metrics: { statement: string; source: string }[];
};

export class ApiError extends Error {
  status: number;
  body: string;
  constructor(message: string, status: number, body = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv && fromEnv.trim().length > 0) return fromEnv.replace(/\/$/, "");
  return "http://localhost:8000";
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = `Request failed with ${res.status}`;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      if (parsed.detail) message = parsed.detail;
    } catch {
      if (text) message = text.slice(0, 300);
    }
    throw new ApiError(message, res.status, text);
  }
  return (await res.json()) as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}${path}`, {
    ...init,
    method: "GET",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}${path}`, {
    ...init,
    method: "POST",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(res);
}

export async function apiPatch<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}${path}`, {
    ...init,
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    body: JSON.stringify(body),
  });
  return handleResponse<T>(res);
}

export function getHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>("/health");
}

export function createEvaluation(payload: EvaluationCreate): Promise<EvaluationRecord> {
  return apiPost<EvaluationRecord>("/api/evaluations", payload);
}

export function listEvaluations(limit = 20, offset = 0): Promise<EvaluationListItem[]> {
  return apiGet<EvaluationListItem[]>(`/api/evaluations?limit=${limit}&offset=${offset}`);
}

export function getEvaluation(id: string): Promise<EvaluationRecord> {
  return apiGet<EvaluationRecord>(`/api/evaluations/${id}`);
}

export function patchEvaluation(
  id: string,
  payload: { explanation_edited?: string; outreach_subject_edited?: string; outreach_body_edited?: string },
): Promise<EvaluationRecord> {
  return apiPatch<EvaluationRecord>(`/api/evaluations/${id}`, payload);
}

export function regenerateOutreach(id: string): Promise<EvaluationRecord> {
  return apiPost<EvaluationRecord>(`/api/evaluations/${id}/outreach/regenerate`, {});
}

export function getCandidate(id: string): Promise<CandidateDetail> {
  return apiGet<CandidateDetail>(`/api/candidates/${id}`);
}

export function getCandidateChunks(id: string): Promise<CandidateChunks> {
  return apiGet<CandidateChunks>(`/api/candidates/${id}/chunks`);
}

export function friendlyError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 422) return "Some fields need attention. Check the highlighted fields.";
    if (e.status === 502) return "The AI service failed. Try again in a moment.";
    if (e.status === 504) return "The AI service timed out. Try again in a moment.";
    if (e.status === 404) return "That record was not found.";
    return e.message;
  }
  if (e instanceof Error) return e.message;
  return "Something went wrong. Try again.";
}

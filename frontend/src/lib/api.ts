/// <reference types="vite/client" />
const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

// ── Error ─────────────────────────────────────────────────────────────────────

export interface ApiErrorBody {
  code: string;
  message: string;
  fields?: Record<string, string>;
}

export class ApiError extends Error {
  constructor(public readonly status: number, public readonly body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
  }
}

// ── Core request ──────────────────────────────────────────────────────────────

async function request<T>(method: string, path: string, body?: unknown, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err =
      data != null && typeof data === "object" && "error" in data &&
      data.error != null && typeof data.error === "object" && "code" in data.error
        ? (data.error as ApiErrorBody)
        : { code: `http_${res.status}`, message: "Unexpected error." };
    throw new ApiError(res.status, err);
  }
  return data as T;
}

async function upload<T>(path: string, formData: FormData, token: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` },
    body: formData,
  });
  const data: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const err =
      data != null && typeof data === "object" && "error" in data &&
      data.error != null && typeof data.error === "object" && "code" in data.error
        ? (data.error as ApiErrorBody)
        : { code: `http_${res.status}`, message: "Unexpected error." };
    throw new ApiError(res.status, err);
  }
  return data as T;
}

// ── Domain types ──────────────────────────────────────────────────────────────

export type Role = "candidate" | "recruiter" | "admin";
export type UserStatus = "active" | "disabled";
export type ResumeStatus = "draft" | "active" | "archived";
export type JobStatus = "draft" | "published" | "closed";
export type AppStatus = "submitted" | "shortlisted" | "rejected" | "hired" | "withdrawn";
export type InviteStatus = "pending" | "accepted" | "rejected";

export interface UserSummary {
  user_id: number; email: string; role: Role; status: UserStatus; created_at: string;
}
export interface AuthResponse {
  access_token: string; token_type: string; expires_in: number; user: UserSummary;
}
export interface CandidateProfile {
  full_name: string; phone: string | null; current_location: string | null;
  total_experience_years: number | null; headline: string | null; user_id: number;
}
export interface RecruiterProfile {
  organization_id: number; full_name: string; title: string | null; phone: string | null; user_id: number;
}
export interface Organization {
  organization_id: number; name: string; slug: string | null; logo_url: string | null; about: string | null;
}
export interface MeResponse {
  user: UserSummary; candidate_profile: CandidateProfile | null;
  recruiter_profile: RecruiterProfile | null; organization: Organization | null;
}
export interface ResumeSummary {
  resume_id: number; title: string; location: string; job_type: string; seniority: string;
  education: string; skills: string[]; certifications: string[]; status: ResumeStatus;
}
export interface ResumeDetail extends ResumeSummary {
  candidate_user_id: number; summary: string; experience: string; is_primary: boolean;
}
export interface JobSummary {
  job_id: number; title: string; location: string; job_type: string; seniority: string;
  education: string; skills: string[]; required_certifications: string[];
  status: JobStatus; published_at: string | null; organization_id: number;
  recruiter_user_id: number; requirement: string; expires_at: string | null;
}
export type JobDetail = JobSummary;
export interface ApplicationEvent {
  event_type: string; from_status: string | null; to_status: string | null;
  actor_user_id: number; note: string | null; created_at: string;
}
export interface ApplicationDetail {
  application_id: number; job_id: number; candidate_user_id: number;
  resume_id: number; status: AppStatus; events: ApplicationEvent[];
}
export interface InviteDetail {
  invite_id: number; job_id: number; resume_id: number;
  candidate_user_id: number; recruiter_user_id: number;
  status: InviteStatus; message: string | null;
}
export interface InviteAcceptResponse {
  invite: InviteDetail; application: ApplicationDetail;
}
export interface NotificationItem {
  notification_id: number; recipient_user_id: number; type: string;
  status: string; title: string; body: string; entity_type: string; entity_id: number;
}
export interface MatchingItem {
  resume_id?: number; job_id?: number; score: number;
  breakdown?: Record<string, number>; reasoning?: string;
}
export interface MatchingResult {
  anchor: { type: string; job_id?: number; resume_id?: number; status: string };
  items: MatchingItem[];
  runtime: { total_ms: number; rerank_applied?: boolean; warnings?: string[] };
}
export interface ParseJobSummary {
  parse_job_id: number; document_id: number; status: string;
  error_code: string | null; error_message: string | null; created_at: string;
}
export interface DocumentDetail {
  document_id: number; filename: string; mime_type: string; size_bytes: number;
  storage_path: string; owner_user_id: number; document_type: string;
  created_at: string; parse_jobs: ParseJobSummary[];
}
export interface Paginated<T> { items: T[]; total: number; limit: number; offset: number; }

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string, role: Role) =>
    request<AuthResponse>("POST", "/api/auth/register", { email, password, role }),
  login: (email: string, password: string) =>
    request<AuthResponse>("POST", "/api/auth/login", { email, password }),
  logout: (token: string) =>
    request<{ message: string }>("POST", "/api/auth/logout", {}, token),
  me: (token: string) => request<MeResponse>("GET", "/api/me", undefined, token),
};

// ── Candidate profile ─────────────────────────────────────────────────────────

export const candidateProfileApi = {
  get: (token: string) => request<CandidateProfile>("GET", "/api/candidate/profile", undefined, token),
  upsert: (data: Partial<CandidateProfile>, token: string) =>
    request<CandidateProfile>("PUT", "/api/candidate/profile", data, token),
};

// ── Recruiter profile ─────────────────────────────────────────────────────────

export const recruiterProfileApi = {
  get: (token: string) => request<RecruiterProfile>("GET", "/api/recruiter/profile", undefined, token),
  upsert: (data: Partial<RecruiterProfile>, token: string) =>
    request<RecruiterProfile>("PUT", "/api/recruiter/profile", data, token),
};

// ── Organizations ─────────────────────────────────────────────────────────────

export const organizationsApi = {
  search: (q: string, token: string) =>
    request<Paginated<Organization>>("GET", `/api/organizations?q=${encodeURIComponent(q)}`, undefined, token),
  get: (id: number, token: string) =>
    request<Organization>("GET", `/api/organizations/${id}`, undefined, token),
  create: (name: string, token: string) =>
    request<Organization>("POST", "/api/organizations", { name }, token),
};

// ── Resumes ───────────────────────────────────────────────────────────────────

export const resumesApi = {
  list: (token: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<ResumeSummary>>("GET", `/api/candidate/resumes${qs ? "?" + qs : ""}`, undefined, token);
  },
  create: (data: Record<string, unknown>, token: string) =>
    request<ResumeDetail>("POST", "/api/candidate/resumes", data, token),
  get: (id: number, token: string) =>
    request<ResumeDetail>("GET", `/api/candidate/resumes/${id}`, undefined, token),
  update: (id: number, data: Record<string, unknown>, token: string) =>
    request<ResumeDetail>("PATCH", `/api/candidate/resumes/${id}`, data, token),
  activate: (id: number, token: string) =>
    request<ResumeDetail>("POST", `/api/candidate/resumes/${id}/activate`, {}, token),
  archive: (id: number, token: string) =>
    request<ResumeDetail>("POST", `/api/candidate/resumes/${id}/archive`, {}, token),
  search: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<ResumeSummary>>("GET", `/api/candidate/resumes/search${qs ? "?" + qs : ""}`, undefined, token);
  },
  semanticSearch: (data: Record<string, unknown>, token: string) =>
    request<Paginated<ResumeSummary>>("POST", "/api/candidate/resumes/semantic-search", data, token),
};

// ── Jobs ──────────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<JobSummary>>("GET", `/api/jobs${qs ? "?" + qs : ""}`, undefined, token);
  },
  create: (data: Record<string, unknown>, token: string) =>
    request<JobDetail>("POST", "/api/jobs", data, token),
  get: (id: number, token: string) =>
    request<JobDetail>("GET", `/api/jobs/${id}`, undefined, token),
  update: (id: number, data: Record<string, unknown>, token: string) =>
    request<JobDetail>("PATCH", `/api/jobs/${id}`, data, token),
  publish: (id: number, token: string) =>
    request<JobDetail>("POST", `/api/jobs/${id}/publish`, {}, token),
  close: (id: number, token: string) =>
    request<JobDetail>("POST", `/api/jobs/${id}/close`, {}, token),
  search: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<JobSummary>>("GET", `/api/jobs/search${qs ? "?" + qs : ""}`, undefined, token);
  },
  semanticSearch: (data: Record<string, unknown>, token: string) =>
    request<Paginated<JobSummary>>("POST", "/api/jobs/semantic-search", data, token),
};

// ── Matching ──────────────────────────────────────────────────────────────────

export const matchingApi = {
  runForJob: (jobId: number, data: Record<string, unknown>, token: string) =>
    request<MatchingResult>("POST", `/api/matching/jobs/${jobId}/run`, data, token),
  runForResume: (resumeId: number, data: Record<string, unknown>, token: string) =>
    request<MatchingResult>("POST", `/api/matching/resumes/${resumeId}/run`, data, token),
};

// ── Applications ──────────────────────────────────────────────────────────────

export const applicationsApi = {
  list: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<ApplicationDetail>>("GET", `/api/applications${qs ? "?" + qs : ""}`, undefined, token);
  },
  create: (jobId: number, resumeId: number, token: string) =>
    request<ApplicationDetail>("POST", "/api/applications", { job_id: jobId, resume_id: resumeId }, token),
  get: (id: number, token: string) =>
    request<ApplicationDetail>("GET", `/api/applications/${id}`, undefined, token),
  updateStatus: (id: number, status: string, token: string) =>
    request<ApplicationDetail>("POST", `/api/applications/${id}/status`, { status }, token),
};

// ── Invites ───────────────────────────────────────────────────────────────────

export const invitesApi = {
  list: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<InviteDetail>>("GET", `/api/invites${qs ? "?" + qs : ""}`, undefined, token);
  },
  create: (jobId: number, resumeId: number, message: string | null, token: string) =>
    request<InviteDetail>("POST", "/api/invites", { job_id: jobId, resume_id: resumeId, message }, token),
  get: (id: number, token: string) =>
    request<InviteDetail>("GET", `/api/invites/${id}`, undefined, token),
  accept: (id: number, token: string) =>
    request<InviteAcceptResponse>("POST", `/api/invites/${id}/accept`, {}, token),
  reject: (id: number, token: string) =>
    request<InviteDetail>("POST", `/api/invites/${id}/reject`, {}, token),
};

// ── Notifications ─────────────────────────────────────────────────────────────

export const notificationsApi = {
  list: (token: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<NotificationItem>>("GET", `/api/notifications${qs ? "?" + qs : ""}`, undefined, token);
  },
  markRead: (id: number, token: string) =>
    request<NotificationItem>("POST", `/api/notifications/${id}/read`, {}, token),
  markAllRead: (token: string) =>
    request<{ updated_count: number }>("POST", "/api/notifications/read-all", {}, token),
};

// ── Documents ─────────────────────────────────────────────────────────────────

export const documentsApi = {
  upload: (file: File, documentType: string, token: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("document_type", documentType);
    return upload<{ document: DocumentDetail; parse_job: ParseJobSummary }>("/api/documents", fd, token);
  },
  get: (id: number, token: string) =>
    request<DocumentDetail>("GET", `/api/documents/${id}`, undefined, token),
  retryParse: (id: number, token: string) =>
    request<ParseJobSummary>("POST", `/api/documents/${id}/parse-jobs`, {}, token),
};

// ── Admin ─────────────────────────────────────────────────────────────────────

export const adminApi = {
  users: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<UserSummary>>("GET", `/api/admin/users${qs ? "?" + qs : ""}`, undefined, token);
  },
  updateUser: (userId: number, status: "active" | "disabled" | "invited", token: string) =>
    request<UserSummary>("PATCH", `/api/admin/users/${userId}`, { status }, token),
  documents: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<DocumentDetail>>("GET", `/api/admin/documents${qs ? "?" + qs : ""}`, undefined, token);
  },
  applications: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<ApplicationDetail>>("GET", `/api/admin/applications${qs ? "?" + qs : ""}`, undefined, token);
  },
  auditLogs: (params: Record<string, string>, token: string) => {
    const qs = new URLSearchParams(params).toString();
    return request<Paginated<Record<string, unknown>>>("GET", `/api/admin/audit-logs${qs ? "?" + qs : ""}`, undefined, token);
  },
};

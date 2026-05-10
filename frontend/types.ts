

export interface Job {
  id: number;
  title: string;
  company: string;
  logo: string;
  salary: string;
  location: string;
  tags: string[]; // Used for matching keywords
  skills?: string[]; // Specific technical skills for matching
  experienceLevel?: string; // e.g., "Junior", "Senior"
  type?: string; // Full-time, Remote, etc.
  postedAt?: string;
  description?: string;
  requirements?: string[];
  benefits?: string[];
}

export interface Category {
  id: number;
  name: string;
  count: number;
  iconName: string;
}

export interface Company {
  id: number;
  name: string;
  logo: string;
  openPositions: number;
}

export interface Testimonial {
  id: number;
  name: string;
  role: string;
  avatar: string;
  content: string;
}

export interface UserCV {
  id: string;
  name: string;
  title: string;
  skills: string[];
  experienceLevel: string;
  location: string;
  lastUpdated: string;
  ownerId?: string;
  details?: any;
}

export interface MatchResult {
  score: number; // 0-100
  matchedSkills: string[];
  reason: string;
}

export interface JobWithMatch extends Job {
  match?: MatchResult;
}

// --- Recruiter Flow Types ---

export interface JobRequirement {
  id: string;
  title: string;
  skills: string[];
  experienceLevel: string;
  location: string;
  createdAt: string;
  openPositions: number;
  // Visual props for the UI
  criteriaList: string[]; // e.g. ["React, TypeScript", "3+ năm kinh nghiệm", "Hà Nội"]
  iconType: 'Code' | 'Megaphone' | 'Server' | 'PenTool'; 
  color: string; // Tailwind color class for bg, e.g. "bg-blue-500"
  ownerId?: string; // ID of the user who created this requirement
}

export interface Candidate {
  id: string;
  name: string;
  headline: string; // e.g. "Senior React Developer"
  avatar: string;
  location: string;
  skills: string[];
  experienceLevel: string; // e.g. "Senior", "Junior"
  yearsOfExperience: number;
  availability: string; // e.g. "Immediate", "2 weeks"
  education?: string;
}

export interface CandidateMatchResult {
  score: number;
  matchedSkills: string[];
  reason: string;
  detailScores?: {
    skills: number;
    experience: number;
    title: number;
    location: number;
    other: number;
  };
}

export interface CandidateWithMatch extends Candidate {
  match?: CandidateMatchResult;
}

// --- Search & Filter Types ---

export type ViewMode = 'grid' | 'list';
export type SortOption = 
  | 'relevance' 
  | 'newest' 
  | 'oldest' 
  | 'salary_high' 
  | 'salary_low'
  | 'exp_high' // Experience High to Low
  | 'exp_low'; // Experience Low to High

export interface FilterOption {
  label: string;
  value: string;
  count?: number;
}

export interface FilterGroup {
  id: string; // key for the filter, e.g. 'level', 'type'
  title: string;
  options: FilterOption[];
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  lastMatchedAt?: string;
}

export interface SearchResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface SearchState {
  q: string;
  location: string;
  filters: Record<string, string[]>;
  sort: SortOption;
  page: number;
}

// --- Auth Types ---

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role?: 'candidate' | 'recruiter' | 'admin';
  
  // Personal Info
  phone?: string;
  gender?: 'Male' | 'Female' | 'Other';
  birthday?: string;
  
  // Career Info
  currentPosition?: string;
  experienceLevel?: string;
  skills?: string[]; // For profile skills tags
  preferredLocation?: string;
  salaryRange?: string;
}

export interface AuthResponse {
  accessToken: string;
  user: User;
}

// --- DTOs ---

export interface CreateCvDto {
//  userId?: string;
  fullname: string;
  preferredName?: string;
  email?: string;
  phone?: string;
  headline?: string;
  avatarUrl?: string;
  location?: {
    city?: string;
    state?: string;
    country?: string;
  };
  summary?: string;
  targetRole?: string;
  salaryExpectation?: string;
  availability?: string;
  employmentType?: string[];
  skills?: {
    name: string;
    level?: string;
    category?: string;
    years?: number;
  }[];
  experiences?: {
    id?: string;
    title: string;
    company: string;
    companyWebsite?: string;
    location?: string;
    from?: string;
    to?: string;
    isCurrent?: boolean;
    employmentType?: string;
    teamSize?: number;
    responsibilities?: string[];
    achievements?: string[];
    tags?: string[];
  }[];
  education?: {
    school: string;
    degree: string;
    major: string;
    from?: string;
    to?: string;
    gpa?: string;
  }[];
  projects?: {
    name: string;
    description?: string;
    role?: string;
    from?: string;
    to?: string;
    techStack?: string[];
    url?: string;
    metrics?: string[];
  }[];
  certifications?: {
    name: string;
    issuer: string;
    issueDate: string;
    expiryDate?: string;
    credentialUrl?: string;
  }[];
  languages?: {
    name: string;
    level: string;
  }[];
  portfolio?: {
    type: string;
    url: string;
    description?: string;
  }[];
  references?: {
    name: string;
    relation?: string;
    contact?: string;
    note?: string;
  }[];
  tags?: string[];
}

// ---------------------------------------------------------------------------
// V2 Prototype types
//
// Mirror of backend pydantic schemas:
//   - backend/schemas/match_v2_schema.py
//   - backend/schemas/v2_catalog_schema.py
// All identifiers are integers (BIGINT in Postgres). Enum string literals
// match the CHECK constraints in backend/db_v2/orm_models.py.
// ---------------------------------------------------------------------------

export type LocationV2 = 'ha_noi' | 'tp_hcm' | 'da_nang';
export type JobTypeV2 = 'remote' | 'fulltime' | 'parttime';
export type SeniorityV2 =
  | 'intern'
  | 'fresher'
  | 'junior'
  | 'mid'
  | 'senior'
  | 'lead';
export type EducationV2 = 'lop_9' | 'lop_12' | 'dai_hoc' | 'thac_si' | 'tien_si';

export type AnchorTypeV2 = 'job' | 'cv';

// ---- Catalog ----

export interface JobV2ListItem {
  job_id: number;
  title: string;
  location: LocationV2;
  job_type: JobTypeV2;
  seniority: SeniorityV2;
  skills: string[];
}

export interface JobV2Detail {
  job_id: number;
  title: string;
  skills: string[];
  requirement: string;
  location: LocationV2;
  job_type: JobTypeV2;
  seniority: SeniorityV2;
  education: EducationV2;
  required_certifications: string[];
}

export interface CVV2ListItem {
  cv_id: number;
  title: string;
  location: LocationV2;
  job_type: JobTypeV2;
  seniority: SeniorityV2;
  skills: string[];
}

export interface CVV2Detail {
  cv_id: number;
  title: string;
  skills: string[];
  summary: string;
  experience: string;
  location: LocationV2;
  job_type: JobTypeV2;
  seniority: SeniorityV2;
  education: EducationV2;
  certifications: string[];
}

export interface JobV2ListResponse {
  items: JobV2ListItem[];
  total: number;
}

export interface CVV2ListResponse {
  items: CVV2ListItem[];
  total: number;
}

// ---- Matching ----

export interface RunMatchingV2Request {
  /** integer in [1, 10] */
  top_k?: number;
  /** float in [0.0, 1.0] */
  min_score?: number;
}

export interface MatchItemV2 {
  rank: number;
  cv_id: number;
  job_id: number;
  final_score: number;
  title_score: number;
  skills_score: number;
  req_exp_score: number;
  req_summary_score: number;
  reasoning: string;
}

export interface RunMatchingV2Response {
  anchor_type: AnchorTypeV2;
  anchor_id: number;
  total_candidates: number;
  total_after_filter: number;
  total_returned: number;
  runtime_ms_total: number;
  runtime_ms_filter: number;
  runtime_ms_scoring: number;
  runtime_ms_sort: number;
  matches: MatchItemV2[];
}

// ---- Catalog semantic search (pgvector-backed) ----
//
// Mirror of backend pydantic schemas in backend/schemas/v2_catalog_schema.py.
// All filters are optional; passing an out-of-enum value yields 422 from BE.

export interface CatalogSearchRequest {
  /** 1..200 chars; trimmed-empty short-circuits to {items:[], total:0}. */
  q: string;
  /** 1..50, default 20 server-side. */
  top_k?: number;
  /** 0..1, default 0.3 server-side. */
  blend_skills?: number;
  location?: LocationV2;
  job_type?: JobTypeV2;
  seniority?: SeniorityV2;
}

export interface JobSearchItem extends JobV2ListItem {
  /** Cosine-blend score, clamped to [0,1] by the backend. */
  score: number;
}

export interface CVSearchItem extends CVV2ListItem {
  score: number;
}

export interface JobSearchResponse {
  items: JobSearchItem[];
  total: number;
}

export interface CVSearchResponse {
  items: CVSearchItem[];
  total: number;
}

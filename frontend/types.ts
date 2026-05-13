// ---------------------------------------------------------------------------
// V2 Prototype types
//
// Mirrors backend pydantic schemas:
//   - backend/schemas/match_v2_schema.py
//   - backend/schemas/v2_catalog_schema.py
//
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

export interface NormalJobSearchItem {
  id: string;
  job_id: string;
  title: string;
  company_name?: string | null;
  company_industry?: string | null;
  department?: string | null;
  location: string;
  location_detail?: Record<string, unknown>;
  job_type: string;
  employment_type?: string[];
  working_model?: string | null;
  seniority?: string | null;
  education?: string | null;
  education_level?: string | null;
  skills: string[];
  requirement: string;
  requirements?: string[];
  responsibilities?: string[];
  categories?: string[];
  tags?: string[];
  salary?: Record<string, unknown>;
  remote?: boolean;
}

export interface NormalCVSearchItem {
  id: string;
  cv_id: string;
  title: string;
  fullname?: string;
  location: string;
  location_detail?: Record<string, unknown>;
  job_type: string;
  employment_type?: string[];
  working_model?: string | null;
  seniority?: string | null;
  education?: string | null;
  skills: string[];
  summary: string;
  experience: string;
  certifications: string[];
  target_role?: string | null;
  availability?: string | null;
  file?: Record<string, unknown>;
}

export interface NormalSearchResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export interface NormalJobSearchParams {
  q?: string;
  keyword?: string;
  title?: string;
  company_name?: string;
  company_industry?: string;
  department?: string;
  location?: string;
  category?: string;
  industry?: string;
  categories?: string;
  tags?: string;
  employmentType?: string;
  experienceLevel?: string;
  salaryMin?: number;
  salaryMax?: number;
  educationLevel?: string;
  workingModel?: string;
  skills?: string;
  page?: number;
  limit?: number;
  sort?: string;
}

export interface NormalCVSearchParams {
  q?: string;
  location?: string;
  desiredCategory?: string;
  desiredIndustry?: string;
  experienceLevel?: string;
  yearsOfExperience?: string;
  educationLevel?: string;
  expectedSalaryMin?: number;
  expectedSalaryMax?: number;
  workingModel?: string;
  availability?: string;
  skills?: string;
  page?: number;
  limit?: number;
  sort?: string;
}

export interface NormalJob {
  id: string;
  created_by: string;
  company_id?: string | null;
  title: string;
  slug?: string | null;
  status: 'draft' | 'published' | 'closed';
  visibility: 'public' | 'private' | 'unlisted';
  company_name?: string | null;
  company_logo_url?: string | null;
  company_website?: string | null;
  company_location?: string | null;
  company_size?: string | null;
  company_industry?: string | null;
  department?: string | null;
  location: Record<string, unknown>;
  employment_type: string[];
  seniority?: string | null;
  team_size?: number | null;
  description?: string | null;
  responsibilities: string[];
  requirements: string[];
  nice_to_have?: string[];
  skills: Array<Record<string, unknown>>;
  experience_years?: number | null;
  education_level?: string | null;
  salary: Record<string, unknown>;
  benefits?: string[];
  bonus?: string | null;
  equity?: string | null;
  apply_url?: string | null;
  apply_email?: string | null;
  recruiter?: Record<string, unknown>;
  how_to_apply?: string | null;
  application_deadline?: string | null;
  tags: string[];
  categories: string[];
  remote: boolean;
  archived: boolean;
  applications_count?: number;
  required_docs?: string[];
  created_at: string;
  updated_at: string;
}

export interface NormalCv {
  id: string;
  created_by: string;
  avatar_url?: string | null;
  fullname: string;
  preferred_name?: string | null;
  email?: string | null;
  phone?: string | null;
  location: Record<string, unknown>;
  headline?: string | null;
  summary?: string | null;
  target_role?: string | null;
  employment_type: string[];
  salary_expectation?: string | null;
  availability?: string | null;
  skills: Array<Record<string, unknown>>;
  experiences: Array<Record<string, unknown>>;
  education: Array<Record<string, unknown>>;
  projects?: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  languages?: Array<Record<string, unknown>>;
  portfolio?: Array<Record<string, unknown>>;
  references?: Array<Record<string, unknown>>;
  status: string;
  visibility: 'public' | 'private' | 'unlisted';
  tags: string[];
  file: Record<string, unknown>;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface NormalJobCreatePayload {
  company_id?: string;
  title: string;
  slug?: string;
  status?: 'draft' | 'published' | 'closed';
  visibility?: 'public' | 'private' | 'unlisted';
  company_name?: string;
  company_logo_url?: string;
  company_website?: string;
  company_location?: string;
  company_size?: string;
  company_industry?: string;
  department?: string;
  location?: Record<string, unknown>;
  employment_type?: string[];
  seniority?: string;
  team_size?: number;
  description?: string;
  responsibilities?: string[];
  requirements?: string[];
  nice_to_have?: string[];
  skills?: Array<Record<string, unknown>>;
  experience_years?: number;
  education_level?: string;
  salary?: Record<string, unknown>;
  benefits?: string[];
  bonus?: string;
  equity?: string;
  apply_url?: string;
  apply_email?: string;
  recruiter?: Record<string, unknown>;
  how_to_apply?: string;
  application_deadline?: string;
  tags?: string[];
  categories?: string[];
  remote?: boolean;
  archived?: boolean;
  required_docs?: string[];
}

export type NormalJobUpdatePayload = Partial<NormalJobCreatePayload>;

export interface NormalCvCreatePayload {
  avatar_url?: string;
  fullname: string;
  preferred_name?: string;
  email?: string;
  phone?: string;
  location?: Record<string, unknown>;
  headline?: string;
  summary?: string;
  target_role?: string;
  employment_type?: string[];
  salary_expectation?: string;
  availability?: string;
  skills?: Array<Record<string, unknown>>;
  experiences?: Array<Record<string, unknown>>;
  education?: Array<Record<string, unknown>>;
  projects?: Array<Record<string, unknown>>;
  certifications?: Array<Record<string, unknown>>;
  languages?: Array<Record<string, unknown>>;
  portfolio?: Array<Record<string, unknown>>;
  references?: Array<Record<string, unknown>>;
  status?: string;
  visibility?: 'public' | 'private' | 'unlisted';
  tags?: string[];
  archived?: boolean;
}

export type NormalCvUpdatePayload = Partial<NormalCvCreatePayload>;

export interface CvExtractResponse {
  extractedText: string;
  cv: Partial<NormalCvCreatePayload> & {
    file?: Record<string, unknown> | null;
  };
  warnings: string[];
}

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

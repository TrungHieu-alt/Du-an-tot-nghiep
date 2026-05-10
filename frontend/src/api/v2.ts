/**
 * V2 prototype API client.
 *
 * Wraps the axios instance from `lib/api.ts` (baseURL already includes `/api`)
 * for the v2 catalog + matching endpoints. Returned shapes are exact mirrors
 * of the backend pydantic schemas in:
 *   - backend/schemas/v2_catalog_schema.py
 *   - backend/schemas/match_v2_schema.py
 */

import api from '../../lib/api';
import { apiRoutes } from '../../lib/api-routes';
import type {
  CatalogSearchRequest,
  CVSearchResponse,
  CVV2Detail,
  CVV2ListResponse,
  JobSearchResponse,
  JobV2Detail,
  JobV2ListResponse,
  RunMatchingV2Request,
  RunMatchingV2Response,
} from '../../types';

export interface ListV2Params {
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// Catalog
// ---------------------------------------------------------------------------

export async function listV2Jobs(params?: ListV2Params): Promise<JobV2ListResponse> {
  const url = apiRoutes.v2.catalog.jobs(params);
  const response = await api.get<JobV2ListResponse>(url);
  return response.data;
}

export async function getV2Job(jobId: number): Promise<JobV2Detail> {
  const url = apiRoutes.v2.catalog.jobById(jobId);
  const response = await api.get<JobV2Detail>(url);
  return response.data;
}

export async function listV2Cvs(params?: ListV2Params): Promise<CVV2ListResponse> {
  const url = apiRoutes.v2.catalog.cvs(params);
  const response = await api.get<CVV2ListResponse>(url);
  return response.data;
}

export async function getV2Cv(cvId: number): Promise<CVV2Detail> {
  const url = apiRoutes.v2.catalog.cvById(cvId);
  const response = await api.get<CVV2Detail>(url);
  return response.data;
}

// ---------------------------------------------------------------------------
// Catalog semantic search (pgvector cosine, blended title + skills)
// ---------------------------------------------------------------------------
//
// Backend short-circuits empty/whitespace `q` to {items:[],total:0} without
// hitting Postgres. Filters (location/job_type/seniority) are applied in the
// SQL CTE before scoring. Score is clamped to [0,1] server-side.

export async function searchV2Jobs(
  body: CatalogSearchRequest
): Promise<JobSearchResponse> {
  const url = apiRoutes.v2.catalog.searchJobs();
  const response = await api.post<JobSearchResponse>(url, body);
  return response.data;
}

export async function searchV2Cvs(
  body: CatalogSearchRequest
): Promise<CVSearchResponse> {
  const url = apiRoutes.v2.catalog.searchCvs();
  const response = await api.post<CVSearchResponse>(url, body);
  return response.data;
}

// ---------------------------------------------------------------------------
// Matching (run-only, synchronous)
// ---------------------------------------------------------------------------

export async function runV2MatchForJob(
  jobId: number,
  body: RunMatchingV2Request = {}
): Promise<RunMatchingV2Response> {
  const url = apiRoutes.v2.matching.runForJob(jobId);
  const response = await api.post<RunMatchingV2Response>(url, body);
  return response.data;
}

export async function runV2MatchForCv(
  cvId: number,
  body: RunMatchingV2Request = {}
): Promise<RunMatchingV2Response> {
  const url = apiRoutes.v2.matching.runForCv(cvId);
  const response = await api.post<RunMatchingV2Response>(url, body);
  return response.data;
}

export const v2Api = {
  listV2Jobs,
  getV2Job,
  listV2Cvs,
  getV2Cv,
  searchV2Jobs,
  searchV2Cvs,
  runV2MatchForJob,
  runV2MatchForCv,
};

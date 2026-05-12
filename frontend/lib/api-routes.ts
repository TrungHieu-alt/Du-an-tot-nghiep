export type RouteId = string | number;

const toPathId = (id: RouteId): string => encodeURIComponent(String(id));

interface PaginationParams {
  limit?: number;
  offset?: number;
}

const buildQueryString = (params?: PaginationParams): string => {
  if (!params) return '';
  const search = new URLSearchParams();
  if (typeof params.limit === 'number') {
    search.set('limit', String(params.limit));
  }
  if (typeof params.offset === 'number') {
    search.set('offset', String(params.offset));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
};

export const apiRoutes = {
  system: {
    health: () => '/health',
    openapi: () => '/openapi.json',
  },
  v2: {
    catalog: {
      jobs: (params?: PaginationParams) =>
        `/v2/prototype/catalog/jobs${buildQueryString(params)}`,
      jobById: (jobId: number) => `/v2/prototype/catalog/jobs/${toPathId(jobId)}`,
      cvs: (params?: PaginationParams) =>
        `/v2/prototype/catalog/cvs${buildQueryString(params)}`,
      cvById: (cvId: number) => `/v2/prototype/catalog/cvs/${toPathId(cvId)}`,
      searchJobs: () => '/v2/prototype/catalog/jobs/search',
      searchCvs: () => '/v2/prototype/catalog/cvs/search',
    },
    matching: {
      runForJob: (jobId: number) => `/v2/prototype/matching/job/${toPathId(jobId)}/run`,
      runForCv: (cvId: number) => `/v2/prototype/matching/cv/${toPathId(cvId)}/run`,
    },
  },
} as const;

export type ApiRoutes = typeof apiRoutes;

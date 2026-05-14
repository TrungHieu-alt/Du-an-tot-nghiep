export type RouteId = string | number;

const toPathId = (id: RouteId): string => encodeURIComponent(String(id));

interface PaginationParams {
  limit?: number;
  offset?: number;
}

type QueryPrimitive = string | number | boolean | undefined | null;

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

const buildAnyQueryString = <T extends object>(params?: T): string => {
  if (!params) return '';
  const search = new URLSearchParams();
  Object.entries(params as Record<string, QueryPrimitive>).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    search.set(key, String(value));
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
};

export const apiRoutes = {
  auth: {
    register: () => '/auth/register',
    login: () => '/auth/login',
    google: () => '/auth/google',
    me: () => '/auth/me',
  },
  system: {
    health: () => '/health',
    openapi: () => '/openapi.json',
  },
  normalSearch: {
    jobs: <T extends object>(params?: T) =>
      `/job/search${buildAnyQueryString(params)}`,
    cvs: <T extends object>(params?: T) =>
      `/cv/search${buildAnyQueryString(params)}`,
    candidates: <T extends object>(params?: T) =>
      `/candidates${buildAnyQueryString(params)}`,
  },
  job: {
    create: () => '/employer/requests',
    my: () => '/employer/requests/my',
    byId: (jobId: RouteId) => `/employer/requests/${toPathId(jobId)}`,
    detail: (jobId: RouteId) => `/job/${toPathId(jobId)}`,
    search: <T extends object>(params?: T) =>
      `/job/search${buildAnyQueryString(params)}`,
    filters: () => '/job/search/filters',
  },
  cv: {
    create: () => '/cvs',
    upload: () => '/cv/upload',
    extractPdf: () => '/cvs/extract-pdf',
    my: () => '/cvs/my',
    byId: (cvId: RouteId) => `/cvs/${toPathId(cvId)}`,
    search: <T extends object>(params?: T) =>
      `/cv/search${buildAnyQueryString(params)}`,
  },
  applications: {
    create: () => '/applications',
    my: <T extends object>(params?: T) =>
      `/applications/me${buildAnyQueryString(params)}`,
    byJob: <T extends object>(jobId: RouteId, params?: T) =>
      `/job/${toPathId(jobId)}/applications${buildAnyQueryString(params)}`,
    status: (applicationId: RouteId) =>
      `/applications/${toPathId(applicationId)}/status`,
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

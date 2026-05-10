export type RouteId = string | number;

const toPathId = (id: RouteId): string => encodeURIComponent(String(id));
const cvPluralSegment = 'cvs';

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
  users: {
    register: () => '/users/register',
    login: () => '/users/login',
    byId: (userId: RouteId) => `/users/${toPathId(userId)}`,
    role: (userId: RouteId) => `/users/${toPathId(userId)}/role`,
  },
  candidate: {
    profile: (userId: RouteId) => `/candidate/profile/${toPathId(userId)}`,
    profiles: () => '/candidate/profiles',
  },
  recruiter: {
    profile: (userId: RouteId) => `/recruiter/profile/${toPathId(userId)}`,
  },
  cv: {
    create: (userId: RouteId) => `/cv/create/${toPathId(userId)}`,
    upload: (userId: RouteId) => `/cv/upload/${toPathId(userId)}`,
    uploadText: (userId: RouteId) => `/cv/upload-text/${toPathId(userId)}`,
    byId: (cvId: RouteId) => `/cv/${toPathId(cvId)}`,
    byUser: (userId: RouteId) => `/cv/user/${toPathId(userId)}`,
    mainByUser: (userId: RouteId) => `/cv/main/user/${toPathId(userId)}`,
    matchJobs: (cvId: RouteId) => `/cv/match/${toPathId(cvId)}/jobs`,
    matchJobDetail: (cvId: RouteId, jobId: RouteId) =>
      `/cv/match/${toPathId(cvId)}/jobs/${toPathId(jobId)}`,
  },
  jobs: {
    list: () => '/jobs',
    create: (recruiterId: RouteId) => `/jobs/create/${toPathId(recruiterId)}`,
    upload: (recruiterId: RouteId) => `/jobs/upload/${toPathId(recruiterId)}`,
    uploadText: (recruiterId: RouteId) => `/jobs/upload-text/${toPathId(recruiterId)}`,
    byId: (jobId: RouteId) => `/jobs/${toPathId(jobId)}`,
    byRecruiter: (recruiterId: RouteId) => `/jobs/recruiter/${toPathId(recruiterId)}`,
    matchCvs: (jobId: RouteId) => `/jobs/match/${toPathId(jobId)}/${cvPluralSegment}`,
    matchCvDetail: (jobId: RouteId, cvId: RouteId) =>
      `/jobs/match/${toPathId(jobId)}/${cvPluralSegment}/${toPathId(cvId)}`,
  },
  matching: {
    runForJob: (jobId: RouteId) => `/matching/job/${toPathId(jobId)}/run`,
    runForCv: (cvId: RouteId) => `/matching/cv/${toPathId(cvId)}/run`,
    runForJobAsync: (jobId: RouteId) => `/matching/job/${toPathId(jobId)}/run/async`,
    runForCvAsync: (cvId: RouteId) => `/matching/cv/${toPathId(cvId)}/run/async`,
    jobStatus: (jobTrackingId: RouteId) => `/matching/jobs/${toPathId(jobTrackingId)}`,
    jobResult: (jobTrackingId: RouteId) => `/matching/jobs/${toPathId(jobTrackingId)}/result`,
    jobMatches: (jobId: RouteId) => `/matching/job/${toPathId(jobId)}/matches`,
    cvMatches: (cvId: RouteId) => `/matching/cv/${toPathId(cvId)}/matches`,
    clearJobMatches: (jobId: RouteId) => `/matching/job/${toPathId(jobId)}/matches`,
    clearCvMatches: (cvId: RouteId) => `/matching/cv/${toPathId(cvId)}/matches`,
  },
  applications: {
    root: () => '/applications/',
    byJob: (jobId: RouteId) => `/applications/job/${toPathId(jobId)}`,
    byCandidate: (candidateId: RouteId) => `/applications/candidate/${toPathId(candidateId)}`,
    status: (appId: RouteId) => `/applications/${toPathId(appId)}/status`,
    byId: (appId: RouteId) => `/applications/${toPathId(appId)}`,
  },
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

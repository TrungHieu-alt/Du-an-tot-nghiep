export type RouteId = string | number;

const toPathId = (id: RouteId): string => encodeURIComponent(String(id));
const cvPluralSegment = 'cvs';

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
} as const;

export type ApiRoutes = typeof apiRoutes;

import {
  JobWithMatch,
  CandidateWithMatch,
  SearchState,
  SearchResponse,
  UserCV,
  JobRequirement,
} from '../types';
import api from '../lib/api';
import { apiRoutes } from '../lib/api-routes';
import { getCurrentUserId } from '../lib/auth-session';
import { isValidContextId } from '../lib/context-id';

type MatchingJobQueued = {
  job_tracking_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
};

type MatchingJobStatus = {
  job_tracking_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  error?: string | null;
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const waitForMatchingJob = async (jobTrackingId: string, maxWaitMs = 120000): Promise<void> => {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const statusRes = await api.get<MatchingJobStatus>(apiRoutes.matching.jobStatus(jobTrackingId));
    const status = statusRes.data?.status;
    if (status === 'succeeded') return;
    if (status === 'failed') {
      throw new Error(statusRes.data?.error || 'Matching job failed');
    }
    await sleep(1000);
  }
  throw new Error('Matching job polling timed out');
};

const formatTimeAgo = (dateInput: string | Date | undefined) => {
  if (!dateInput) return 'Vừa xong';
  const date = new Date(dateInput);
  const now = new Date();
  const diff = (now.getTime() - date.getTime()) / 1000;

  if (diff < 60) return 'Vừa xong';
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)} ngày trước`;
  return date.toLocaleDateString('vi-VN');
};

const extractFieldFromPreview = (text: string, label: string): string => {
  if (!text) return '';
  const regex = new RegExp(`${label}:\\s*([^\\n]+)`, 'i');
  const match = text.match(regex);
  return match ? match[1].trim() : '';
};

const getLastMatchedAt = (items: any[]): string | undefined => {
  const stamps = items
    .map((x) => x?.updated_at)
    .filter((x): x is string => typeof x === 'string' && x.length > 0)
    .map((x) => new Date(x).getTime())
    .filter((x) => Number.isFinite(x) && x > 0);
  if (!stamps.length) return undefined;
  return new Date(Math.max(...stamps)).toISOString();
};

export const searchJobsApi = async (
  params: SearchState,
  cvId?: string,
  options?: { forceRematch?: boolean }
): Promise<SearchResponse<JobWithMatch>> => {
  try {
    if (isValidContextId(cvId)) {
      let response = await api.get(apiRoutes.matching.cvMatches(cvId), {
        params: { min_score: 0.0, limit: 20, skip: 0 },
      });
      let rawItems = Array.isArray(response.data?.matches) ? response.data.matches : [];

      // Recompute only when no persisted matches exist, or user explicitly forces rematch.
      if (rawItems.length === 0 || options?.forceRematch) {
        const enqueueRes = await api.post<MatchingJobQueued>(
          apiRoutes.matching.runForCvAsync(cvId),
          { top_k: 20, min_score: 0.0 }
        );
        const jobTrackingId = enqueueRes.data?.job_tracking_id;
        if (!jobTrackingId) {
          throw new Error('Missing job_tracking_id from async matching enqueue');
        }
        await waitForMatchingJob(jobTrackingId);
        response = await api.get(apiRoutes.matching.cvMatches(cvId), {
          params: { min_score: 0.0, limit: 20, skip: 0 },
        });
        rawItems = Array.isArray(response.data?.matches) ? response.data.matches : [];
      }

      const mapped: JobWithMatch[] = rawItems.map((match: any) => {
        const previewText = match.metadata?.reason || match.job?.full_text || '';
        const title = match.job?.title || match.job_title || `Job ${match.job_id ?? ''}`;
        const company = match.job?.company_name || 'Công ty';
        const location = match.job?.location || extractFieldFromPreview(previewText, 'Location') || 'Việt Nam';
        const skills = Array.isArray(match.job?.skills)
          ? match.job.skills
          : extractFieldFromPreview(previewText, 'Skills')
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean);

        return {
          id: match.job_id,
          title,
          company,
          logo: `https://ui-avatars.com/api/?name=${encodeURIComponent(company)}&background=random&color=fff`,
          salary: 'Thỏa thuận',
          location,
          tags: [],
          skills,
          experienceLevel: match.job?.experience_level || '',
          type: match.job?.job_type || '',
          postedAt: 'Vừa xong',
          description: previewText,
          requirements: [],
          benefits: [],
          match: {
            score: Math.round((match.score ?? 0) * 100),
            matchedSkills: [],
            reason: match.metadata?.reason || 'Không có mô tả',
          },
        };
      });

      return {
        data: mapped,
        meta: {
          page: params.page || 1,
          limit: 10,
          total: mapped.length,
          totalPages: 1,
          lastMatchedAt: getLastMatchedAt(rawItems),
        },
      };
    }

    const response = await api.get(apiRoutes.jobs.list());
    const rawItems = Array.isArray(response.data) ? response.data : [];
    const jobs: JobWithMatch[] = rawItems.map((item: any) => ({
      id: item.job_id ?? item.id,
      title: item.title || 'Công việc không tên',
      company: 'Công ty ẩn danh',
      logo: `https://ui-avatars.com/api/?name=${encodeURIComponent(item.title || 'Job')}&background=random`,
      salary:
        item.salary_min !== undefined || item.salary_max !== undefined
          ? `${item.salary_min ?? '?'} - ${item.salary_max ?? '?'} ${item.currency || ''}`
          : 'Thỏa thuận',
      location: item.location || 'Việt Nam',
      tags: [],
      skills: Array.isArray(item.skills) ? item.skills : [],
      experienceLevel: item.experience_level || '',
      type: item.job_type || '',
      postedAt: formatTimeAgo(item.created_at || item.updated_at),
      description: item.full_text,
      requirements: [],
      benefits: [],
    }));

    return {
      data: jobs,
      meta: {
        page: params.page || 1,
        limit: 10,
        total: jobs.length,
        totalPages: 1,
      },
    };
  } catch (error) {
    console.error('fetch jobs error', error);
    return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
  }
};

export const searchCandidatesApi = async (
  params: SearchState,
  reqId?: string,
  options?: { forceRematch?: boolean }
): Promise<SearchResponse<CandidateWithMatch>> => {
  try {
    let rawList: any[] = [];

    if (isValidContextId(reqId)) {
      try {
        let response = await api.get(apiRoutes.matching.jobMatches(reqId), {
          params: { min_score: 0.0, limit: 20, skip: 0 },
        });
        rawList = Array.isArray(response.data?.matches) ? response.data.matches : [];

        // Recompute only when no persisted matches exist, or user explicitly forces rematch.
        if (rawList.length === 0 || options?.forceRematch) {
          const enqueueRes = await api.post<MatchingJobQueued>(
            apiRoutes.matching.runForJobAsync(reqId),
            { top_k: 20, min_score: 0.0 }
          );
          const jobTrackingId = enqueueRes.data?.job_tracking_id;
          if (!jobTrackingId) {
            throw new Error('Missing job_tracking_id from async matching enqueue');
          }
          await waitForMatchingJob(jobTrackingId);
          response = await api.get(apiRoutes.matching.jobMatches(reqId), {
            params: { min_score: 0.0, limit: 20, skip: 0 },
          });
          rawList = Array.isArray(response.data?.matches) ? response.data.matches : [];
        }

        const candidates: CandidateWithMatch[] = rawList.map((match: any) => {
          const preview = match.metadata?.reason || '';
          const skills = Array.isArray(match.cv?.skills) ? match.cv.skills : [];
          return {
            id: String(match.user_id ?? match.cv_id),
            name: match.cv?.title || 'Ứng viên',
            headline: match.cv?.summary || 'Open to work',
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(match.cv?.title || 'U')}&background=random`,
            location: match.cv?.location || extractFieldFromPreview(preview, 'Location') || 'Việt Nam',
            skills,
            experienceLevel: 'Mid-Level',
            yearsOfExperience: 0,
            availability: 'Sẵn sàng',
            education: '',
            match: {
              score: Math.round((match.score ?? 0) * 100),
              matchedSkills: [],
              reason: match.metadata?.reason || preview,
            },
          };
        });

        return {
          data: candidates,
          meta: {
            page: params.page || 1,
            limit: 10,
            total: candidates.length,
            totalPages: 1,
            lastMatchedAt: getLastMatchedAt(rawList),
          },
        };
      } catch (error: any) {
        console.error('Candidate matching endpoint failed in match mode', error);
        return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
      }
    }

    const response = await api.get(apiRoutes.candidate.profiles());
    rawList = Array.isArray(response.data) ? response.data : [];

    let candidates: CandidateWithMatch[] = rawList.map((item: any) => ({
      id: String(item.user_id),
      name: item.full_name || 'Ứng viên',
      headline: item.summary || 'Open to work',
      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(item.full_name || 'User')}&background=random`,
      location: item.location || 'Việt Nam',
      skills: Array.isArray(item.skills) ? item.skills : [],
      experienceLevel: item.experience_years >= 5 ? 'Senior' : item.experience_years >= 2 ? 'Mid-Level' : 'Junior',
      yearsOfExperience: Number(item.experience_years || 0),
      availability: 'Sẵn sàng',
      education: '',
    }));

    return {
      data: candidates,
      meta: {
        page: params.page || 1,
        limit: 10,
        total: candidates.length,
        totalPages: 1,
      },
    };
  } catch (error) {
    console.error('searchCandidatesApi failed:', error);
    return { data: [], meta: { page: 1, limit: 10, total: 0, totalPages: 0 } };
  }
};

const requireCurrentUserId = (): string => {
  const userId = getCurrentUserId();
  if (!userId) {
    throw new Error('Missing authenticated user id');
  }
  return userId;
};

export const createRequirement = async (req: JobRequirement): Promise<JobRequirement> => {
  const recruiterId = requireCurrentUserId();
  const response = await api.post(apiRoutes.jobs.create(recruiterId), req);
  return response.data;
};

export const updateRequirement = async (id: string, payload: Partial<JobRequirement>): Promise<JobRequirement> => {
  const response = await api.put(apiRoutes.jobs.byId(id), payload);
  return response.data;
};

export const deleteRequirement = async (id: string): Promise<boolean> => {
  const response = await api.delete(apiRoutes.jobs.byId(id));
  return response.status === 200;
};

export const createCv = async (cv: UserCV): Promise<UserCV> => {
  const userId = requireCurrentUserId();
  const response = await api.post(apiRoutes.cv.create(userId), cv);
  return response.data;
};

export const updateCv = async (id: string, payload: Partial<UserCV>): Promise<UserCV> => {
  const response = await api.put(apiRoutes.cv.byId(id), payload);
  return response.data;
};

export const deleteCv = async (id: string): Promise<boolean> => {
  const response = await api.delete(apiRoutes.cv.byId(id));
  return response.status === 200;
};

export const sendChatMessage = async (_message: string): Promise<string> => {
  return 'Chatbot hiện chưa khả dụng theo backend contract hiện tại.';
};

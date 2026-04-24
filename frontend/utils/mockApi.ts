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
import { calculateCandidateMatch, MOCK_REQUIREMENTS } from './matchingCandidates';
import { getCurrentUserId } from '../lib/auth-session';

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

export const searchJobsApi = async (
  params: SearchState,
  cvId?: string
): Promise<SearchResponse<JobWithMatch>> => {
  try {
    if (cvId) {
      const response = await api.get(apiRoutes.cv.matchJobs(cvId), {
        params: { top_k: 20 },
      });
      const rawItems = Array.isArray(response.data) ? response.data : [];
      const mapped: JobWithMatch[] = rawItems.map((match: any) => {
        const previewText = match.reason || match.jd?.full_text || '';
        const title = match.jd?.title || match.job_title || `Job ${match.job_id ?? ''}`;
        const company = match.jd?.company_name || 'Công ty';
        const location = match.jd?.location || extractFieldFromPreview(previewText, 'Location') || 'Việt Nam';
        const skills = Array.isArray(match.jd?.skills)
          ? match.jd.skills
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
          experienceLevel: match.jd?.experience_level || '',
          type: match.jd?.job_type || '',
          postedAt: 'Vừa xong',
          description: previewText,
          requirements: [],
          benefits: [],
          match: {
            score: Math.round((match.llm_score ?? match.score ?? 0) * (match.llm_score ? 1 : 100)),
            matchedSkills: [],
            reason: match.reason || 'Không có mô tả',
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
  reqId?: string
): Promise<SearchResponse<CandidateWithMatch>> => {
  try {
    let rawList: any[] = [];

    if (reqId) {
      try {
        const response = await api.get(apiRoutes.jobs.matchCvs(reqId), { params: { top_k: 20 } });
        rawList = Array.isArray(response.data) ? response.data : [];

        const candidates: CandidateWithMatch[] = rawList.map((match: any) => {
          const preview = match.reason || match.cv?.full_text || '';
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
              score: Math.round((match.llm_score ?? match.score ?? 0) * (match.llm_score ? 1 : 100)),
              matchedSkills: [],
              reason: match.reason || preview,
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
          },
        };
      } catch (error: any) {
        console.warn('Candidate matching endpoint failed, falling back to candidate profiles', error);
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

    if (reqId && candidates.length) {
      let req = MOCK_REQUIREMENTS.find((r) => r.id === reqId);
      if (!req) {
        try {
          const stored = JSON.parse(localStorage.getItem('demo_requirements') || '[]');
          req = stored.find((r: any) => r.id === reqId);
        } catch {
          req = undefined;
        }
      }

      if (req) {
        candidates = candidates.map((c) => ({ ...c, match: calculateCandidateMatch(req!, c) }));
        if (params.sort === 'relevance') {
          candidates.sort((a, b) => (b.match?.score || 0) - (a.match?.score || 0));
        }
      }
    }

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

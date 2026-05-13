import { describe, expect, it, vi, beforeEach } from 'vitest';

// Mock the axios instance BEFORE importing v2 module so the import picks up the mock.
vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from '../../lib/api';
import {
  getV2Cv,
  getV2Job,
  listV2Cvs,
  listV2Jobs,
  runV2MatchForCv,
  runV2MatchForJob,
  searchCvs,
  searchJobs,
  searchV2Cvs,
  searchV2Jobs,
} from './v2';
import type {
  CVSearchResponse,
  CVV2Detail,
  CVV2ListResponse,
  JobSearchResponse,
  JobV2Detail,
  JobV2ListResponse,
  NormalJobSearchItem,
  NormalSearchResponse,
  RunMatchingV2Response,
} from '../../types';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('v2Api', () => {
  beforeEach(() => {
    mockedApi.get.mockReset();
    mockedApi.post.mockReset();
  });

  describe('normal search', () => {
    it('GETs the normal job search endpoint with query params', async () => {
      const payload: NormalSearchResponse<NormalJobSearchItem> = {
        items: [
          {
            id: '4001',
            job_id: '4001',
            title: 'Marketing Executive',
            location: 'tp_hcm',
            job_type: 'fulltime',
            seniority: 'junior',
            education: 'dai_hoc',
            skills: ['content'],
            requirement: 'Run campaigns',
            employment_type: ['fulltime'],
            working_model: 'onsite',
          },
        ],
        total: 1,
        page: 1,
        limit: 10,
        totalPages: 1,
      };
      mockedApi.get.mockResolvedValueOnce({ data: payload });

      const result = await searchJobs({
        q: 'marketing',
        industry: 'marketing',
        location: 'tp_hcm',
        page: 1,
        limit: 10,
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/job/search?q=marketing&industry=marketing&location=tp_hcm&page=1&limit=10'
      );
      expect(result).toEqual(payload);
    });

    it('GETs the normal CV search endpoint with general filters', async () => {
      mockedApi.get.mockResolvedValueOnce({
        data: { items: [], total: 0, page: 1, limit: 10, totalPages: 0 },
      });

      await searchCvs({
        q: 'sales',
        desiredIndustry: 'sales',
        skills: 'communication',
        yearsOfExperience: '2_5',
      });

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/cv/search?q=sales&desiredIndustry=sales&skills=communication&yearsOfExperience=2_5'
      );
    });
  });

  describe('listV2Jobs', () => {
    it('GETs the catalog list URL with no params and returns the body', async () => {
      const payload: JobV2ListResponse = {
        items: [
          {
            job_id: 4001,
            title: 'Senior Backend',
            location: 'ha_noi',
            job_type: 'remote',
            seniority: 'senior',
            skills: ['python'],
          },
        ],
        total: 1,
      };
      mockedApi.get.mockResolvedValueOnce({ data: payload });

      const result = await listV2Jobs();

      expect(mockedApi.get).toHaveBeenCalledWith('/v2/prototype/catalog/jobs');
      expect(result).toEqual(payload);
    });

    it('forwards limit/offset as query string', async () => {
      mockedApi.get.mockResolvedValueOnce({ data: { items: [], total: 0 } });

      await listV2Jobs({ limit: 10, offset: 20 });

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/v2/prototype/catalog/jobs?limit=10&offset=20'
      );
    });
  });

  describe('getV2Job', () => {
    it('GETs the detail URL with the integer id', async () => {
      const detail: JobV2Detail = {
        job_id: 4001,
        title: 'Senior Backend',
        skills: ['python'],
        requirement: '3+ năm',
        location: 'ha_noi',
        job_type: 'remote',
        seniority: 'senior',
        education: 'dai_hoc',
        required_certifications: [],
      };
      mockedApi.get.mockResolvedValueOnce({ data: detail });

      const result = await getV2Job(4001);

      expect(mockedApi.get).toHaveBeenCalledWith('/v2/prototype/catalog/jobs/4001');
      expect(result).toEqual(detail);
    });
  });

  describe('listV2Cvs', () => {
    it('GETs the catalog list URL', async () => {
      const payload: CVV2ListResponse = {
        items: [
          {
            cv_id: 3001,
            title: 'Junior Backend',
            location: 'ha_noi',
            job_type: 'fulltime',
            seniority: 'junior',
            skills: [],
          },
        ],
        total: 1,
      };
      mockedApi.get.mockResolvedValueOnce({ data: payload });

      const result = await listV2Cvs({ limit: 5 });

      expect(mockedApi.get).toHaveBeenCalledWith(
        '/v2/prototype/catalog/cvs?limit=5'
      );
      expect(result).toEqual(payload);
    });
  });

  describe('getV2Cv', () => {
    it('GETs the detail URL with the integer id', async () => {
      const detail: CVV2Detail = {
        cv_id: 3001,
        title: 'Junior Backend',
        skills: ['python'],
        summary: '',
        experience: '',
        location: 'ha_noi',
        job_type: 'fulltime',
        seniority: 'junior',
        education: 'dai_hoc',
        certifications: [],
      };
      mockedApi.get.mockResolvedValueOnce({ data: detail });

      const result = await getV2Cv(3001);

      expect(mockedApi.get).toHaveBeenCalledWith('/v2/prototype/catalog/cvs/3001');
      expect(result).toEqual(detail);
    });
  });

  describe('runV2MatchForJob', () => {
    it('POSTs to the run endpoint with the request body', async () => {
      const response: RunMatchingV2Response = {
        anchor_type: 'job',
        anchor_id: 4001,
        total_candidates: 5,
        total_after_filter: 3,
        total_returned: 1,
        runtime_ms_total: 12.3,
        runtime_ms_filter: 1.1,
        runtime_ms_scoring: 9.0,
        runtime_ms_sort: 0.2,
        matches: [
          {
            rank: 1,
            cv_id: 3001,
            job_id: 4001,
            final_score: 0.92,
            title_score: 0.9,
            skills_score: 0.95,
            req_exp_score: 0.9,
            req_summary_score: 0.9,
            reasoning: 'ok',
          },
        ],
      };
      mockedApi.post.mockResolvedValueOnce({ data: response });

      const body = { top_k: 5, min_score: 0.7 };
      const result = await runV2MatchForJob(4001, body);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/matching/job/4001/run',
        body
      );
      expect(result).toEqual(response);
    });

    it('defaults the body to an empty object when omitted', async () => {
      mockedApi.post.mockResolvedValueOnce({
        data: {
          anchor_type: 'job',
          anchor_id: 4001,
          total_candidates: 0,
          total_after_filter: 0,
          total_returned: 0,
          runtime_ms_total: 0,
          runtime_ms_filter: 0,
          runtime_ms_scoring: 0,
          runtime_ms_sort: 0,
          matches: [],
        },
      });

      await runV2MatchForJob(4001);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/matching/job/4001/run',
        {}
      );
    });
  });

  describe('searchV2Jobs', () => {
    it('POSTs to the search endpoint with the query body', async () => {
      const payload: JobSearchResponse = {
        items: [
          {
            job_id: 4001,
            title: 'Senior Backend',
            location: 'ha_noi',
            job_type: 'remote',
            seniority: 'senior',
            skills: ['python'],
            score: 0.83,
          },
        ],
        total: 1,
      };
      mockedApi.post.mockResolvedValueOnce({ data: payload });

      const body = { q: 'backend', top_k: 10 };
      const result = await searchV2Jobs(body);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/catalog/jobs/search',
        body
      );
      expect(result).toEqual(payload);
      expect(result.items[0].score).toBeCloseTo(0.83, 5);
    });

    it('forwards optional filters in the body', async () => {
      mockedApi.post.mockResolvedValueOnce({ data: { items: [], total: 0 } });

      const body = {
        q: 'backend',
        top_k: 5,
        blend_skills: 0.4,
        location: 'ha_noi' as const,
        job_type: 'remote' as const,
        seniority: 'senior' as const,
      };
      await searchV2Jobs(body);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/catalog/jobs/search',
        body
      );
    });
  });

  describe('searchV2Cvs', () => {
    it('POSTs to the cv search endpoint with the query body', async () => {
      const payload: CVSearchResponse = {
        items: [
          {
            cv_id: 3001,
            title: 'Senior Backend',
            location: 'ha_noi',
            job_type: 'remote',
            seniority: 'senior',
            skills: [],
            score: 0.77,
          },
        ],
        total: 1,
      };
      mockedApi.post.mockResolvedValueOnce({ data: payload });

      const result = await searchV2Cvs({ q: 'python', seniority: 'senior' });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/catalog/cvs/search',
        { q: 'python', seniority: 'senior' }
      );
      expect(result).toEqual(payload);
    });
  });

  describe('runV2MatchForCv', () => {
    it('POSTs to the run endpoint with the request body', async () => {
      mockedApi.post.mockResolvedValueOnce({
        data: {
          anchor_type: 'cv',
          anchor_id: 3001,
          total_candidates: 0,
          total_after_filter: 0,
          total_returned: 0,
          runtime_ms_total: 0,
          runtime_ms_filter: 0,
          runtime_ms_scoring: 0,
          runtime_ms_sort: 0,
          matches: [],
        },
      });

      await runV2MatchForCv(3001, { top_k: 10, min_score: 0.5 });

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/v2/prototype/matching/cv/3001/run',
        { top_k: 10, min_score: 0.5 }
      );
    });
  });
});

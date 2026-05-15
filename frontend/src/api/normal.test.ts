import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  }));

import api from '../../lib/api';
import {
  createCv,
  createJob,
  createApplication,
  extractCvPdf,
  getJob,
  getCv,
  listJobApplications,
  listMyApplications,
  listMyCvs,
  searchCvs,
  searchJobs,
  updateApplicationStatus,
} from './normal';
import type {
  NormalApplication,
  NormalCVSearchItem,
  NormalCv,
  NormalJobSearchItem,
  NormalSearchResponse,
} from '../../types';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
};

describe('normal API client', () => {
  beforeEach(() => {
    mockedApi.get.mockReset();
    mockedApi.post.mockReset();
    mockedApi.patch.mockReset();
    mockedApi.put.mockReset();
  });

  it('uses the public normal job search endpoint with no V2/scenario path', async () => {
    const payload: NormalSearchResponse<NormalJobSearchItem> = {
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    };
    mockedApi.get.mockResolvedValueOnce({ data: payload });

    const result = await searchJobs({});

    expect(mockedApi.get).toHaveBeenCalledWith('/job/search');
    expect(mockedApi.get.mock.calls[0][0]).not.toContain('/v2/prototype');
    expect(mockedApi.get.mock.calls[0][0]).not.toContain('scenario');
    expect(result).toEqual(payload);
  });

  it('uses the public normal CV search endpoint with no V2/scenario path', async () => {
    const payload: NormalSearchResponse<NormalCVSearchItem> = {
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    };
    mockedApi.get.mockResolvedValueOnce({ data: payload });

    const result = await searchCvs({});

    expect(mockedApi.get).toHaveBeenCalledWith('/cv/search');
    expect(mockedApi.get.mock.calls[0][0]).not.toContain('/v2/prototype');
    expect(mockedApi.get.mock.calls[0][0]).not.toContain('scenario');
    expect(result).toEqual(payload);
  });

  it('serializes normalized normal CV filter query values', async () => {
    const payload: NormalSearchResponse<NormalCVSearchItem> = {
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    };
    mockedApi.get.mockResolvedValueOnce({ data: payload });

    await searchCvs({
      q: 'Python FastAPI',
      desiredIndustry: 'information_technology',
      occupationGroup: 'software_engineering',
      careerLevel: 'junior,middle',
      skills: 'python,fastapi',
      educationLevel: 'bachelor',
      languageLevel: 'intermediate',
      sort: 'yearsOfExperience_desc',
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/cv/search?q=Python+FastAPI&desiredIndustry=information_technology&occupationGroup=software_engineering&careerLevel=junior%2Cmiddle&skills=python%2Cfastapi&educationLevel=bachelor&languageLevel=intermediate&sort=yearsOfExperience_desc'
    );
  });

  it('creates CVs without sending createdBy or embedding and maps response system fields', async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: {
        id: 'cv-1',
        createdBy: 'user-1',
        fullname: 'Nguyễn Văn An',
        location: {},
        employmentType: [],
        skills: [],
        experiences: [],
        education: [],
        certifications: [],
        status: 'draft',
        visibility: 'private',
        tags: [],
        version: 1,
        file: {},
        archived: false,
        createdAt: '2026-05-15T00:00:00Z',
        updatedAt: '2026-05-15T00:00:00Z',
      },
    });

    const result = await createCv('token', {
      fullname: 'Nguyễn Văn An',
      visibility: 'private',
      archived: false,
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/cvs',
      {
        fullname: 'Nguyễn Văn An',
        visibility: 'private',
        archived: false,
      },
      {
        headers: { Authorization: 'Bearer token' },
      }
    );
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('createdBy');
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('embedding');
    expect(result.created_by).toBe('user-1');
    expect(result.created_at).toBe('2026-05-15T00:00:00Z');
    expect(result.updated_at).toBe('2026-05-15T00:00:00Z');
    expect(result.visibility).toBe('private');
    expect(result.archived).toBe(false);
    expect(result.version).toBe(1);
  });

  it('creates jobs without sending createdBy or embedding and maps response system fields', async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: {
        id: 'job-1',
        createdBy: 'recruiter-1',
        title: 'Lập trình viên Backend Python',
        status: 'draft',
        visibility: 'private',
        location: {},
        employmentType: ['fulltime'],
        responsibilities: [],
        requirements: [],
        skills: [],
        salary: {},
        tags: [],
        categories: [],
        remote: false,
        archived: false,
        applicationsCount: 0,
        publishedBy: null,
        approvedAt: null,
        approvedBy: null,
        version: 1,
        createdAt: '2026-05-15T00:00:00Z',
        updatedAt: '2026-05-15T00:00:00Z',
      },
    });

    const result = await createJob('token', {
      title: 'Lập trình viên Backend Python',
      visibility: 'private',
      archived: false,
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/employer/requests',
      {
        title: 'Lập trình viên Backend Python',
        visibility: 'private',
        archived: false,
      },
      {
        headers: { Authorization: 'Bearer token' },
      }
    );
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('createdBy');
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('embedding');
    expect(result.created_by).toBe('recruiter-1');
    expect(result.applications_count).toBe(0);
    expect(result.published_by).toBeNull();
    expect(result.approved_at).toBeNull();
    expect(result.approved_by).toBeNull();
    expect(result.created_at).toBe('2026-05-15T00:00:00Z');
    expect(result.updated_at).toBe('2026-05-15T00:00:00Z');
  });

  it('gets public CV detail without an auth header', async () => {
    const payload = {
      id: 'cv-1',
      created_by: 'user-1',
      fullname: 'Public Candidate',
      location: {},
      employment_type: [],
      skills: [],
      experiences: [],
      education: [],
      certifications: [],
      status: 'published',
      visibility: 'public',
      tags: [],
      file: {},
      archived: false,
      created_at: '2026-05-13T00:00:00Z',
      updated_at: '2026-05-13T00:00:00Z',
    } satisfies NormalCv;
    mockedApi.get.mockResolvedValueOnce({ data: payload });

    await getCv(null, 'cv-1');

    expect(mockedApi.get).toHaveBeenCalledWith('/cvs/cv-1', {
      headers: undefined,
    });
  });

  it('gets public job detail through the normal job endpoint', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        id: 'job-1',
        created_by: 'recruiter-1',
        title: 'Backend Engineer',
        status: 'published',
        visibility: 'public',
        location: {},
        employmentType: ['fulltime'],
        responsibilities: [],
        requirements: [],
        skills: [],
        salary: {},
        tags: [],
        categories: [],
        remote: false,
        archived: false,
        created_at: '2026-05-14T00:00:00Z',
        updated_at: '2026-05-14T00:00:00Z',
      },
    });

    await getJob('job-1', null);

    expect(mockedApi.get).toHaveBeenCalledWith('/job/job-1', {
      headers: undefined,
    });
  });

  it('keeps my CVs behind an auth header', async () => {
    mockedApi.get.mockResolvedValueOnce({ data: [] });

    await listMyCvs('token');

    expect(mockedApi.get).toHaveBeenCalledWith('/cvs/my', {
      headers: { Authorization: 'Bearer token' },
    });
  });

  it('posts PDF files to the CV extraction preview endpoint without saving', async () => {
    const file = new File(['%PDF-1.4'], 'cv.pdf', { type: 'application/pdf' });
    mockedApi.post.mockResolvedValueOnce({
      data: {
        extractedText: 'Nguyen Van A',
        cv: { fullname: 'Nguyen Van A', employmentType: ['fulltime'] },
        warnings: [],
      },
    });

    const result = await extractCvPdf('token', file);

    expect(mockedApi.post.mock.calls[0][0]).toBe('/cvs/extract-pdf');
    expect(mockedApi.post.mock.calls[0][1]).toBeInstanceOf(FormData);
    expect(mockedApi.post.mock.calls[0][2]).toEqual({
      headers: {
        Authorization: 'Bearer token',
        'Content-Type': 'multipart/form-data',
      },
    });
    expect(result.cv.fullname).toBe('Nguyen Van A');
    expect(result.cv.employment_type).toEqual(['fulltime']);
  });

  it('creates normal applications with jobId and cvId only, no matching fields', async () => {
    const payload: NormalApplication = {
      id: 'app-1',
      jobId: 'job-1',
      cvId: 'cv-1',
      candidateId: 'candidate-1',
      recruiterId: 'recruiter-1',
      status: 'submitted',
      coverLetter: 'Hello',
      createdAt: '2026-05-14T00:00:00Z',
      updatedAt: '2026-05-14T00:00:00Z',
      job: { id: 'job-1', title: 'Backend Engineer', companyName: 'Demo Co' },
      cv: { id: 'cv-1', fullname: 'Nguyen Van A', headline: 'Backend Candidate' },
    };
    mockedApi.post.mockResolvedValueOnce({ data: payload });

    const result = await createApplication('token', {
      jobId: 'job-1',
      cvId: 'cv-1',
      coverLetter: 'Hello',
    });

    expect(mockedApi.post).toHaveBeenCalledWith(
      '/applications',
      {
        jobId: 'job-1',
        cvId: 'cv-1',
        coverLetter: 'Hello',
      },
      {
        headers: { Authorization: 'Bearer token' },
      }
    );
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('matchScore');
    expect(mockedApi.post.mock.calls[0][1]).not.toHaveProperty('matchingWeights');
    expect(result).toEqual(payload);
  });

  it('lists candidate and recruiter application endpoints without V2 paths', async () => {
    mockedApi.get.mockResolvedValue({ data: { items: [], total: 0, page: 1, limit: 10, totalPages: 0 } });

    await listMyApplications('token', { page: 1, limit: 10 });
    await listJobApplications('token', 'job-1', { limit: 50 });

    expect(mockedApi.get).toHaveBeenNthCalledWith(1, '/applications/me?page=1&limit=10', {
      headers: { Authorization: 'Bearer token' },
    });
    expect(mockedApi.get).toHaveBeenNthCalledWith(2, '/job/job-1/applications?limit=50', {
      headers: { Authorization: 'Bearer token' },
    });
    expect(mockedApi.get.mock.calls[0][0]).not.toContain('/v2/prototype');
    expect(mockedApi.get.mock.calls[1][0]).not.toContain('/v2/prototype');
  });

  it('updates normal application status without score fields', async () => {
    const payload: NormalApplication = {
      id: 'app-1',
      jobId: 'job-1',
      cvId: 'cv-1',
      candidateId: 'candidate-1',
      recruiterId: 'recruiter-1',
      status: 'reviewing',
      coverLetter: null,
      createdAt: '2026-05-14T00:00:00Z',
      updatedAt: '2026-05-14T00:00:00Z',
      job: { id: 'job-1', title: 'Backend Engineer' },
      cv: { id: 'cv-1', fullname: 'Nguyen Van A' },
    };
    mockedApi.patch.mockResolvedValueOnce({ data: payload });

    await updateApplicationStatus('token', 'app-1', 'reviewing');

    expect(mockedApi.patch).toHaveBeenCalledWith(
      '/applications/app-1/status',
      { status: 'reviewing' },
      {
        headers: { Authorization: 'Bearer token' },
      }
    );
    expect(mockedApi.patch.mock.calls[0][1]).not.toHaveProperty('recommendation');
    expect(mockedApi.patch.mock.calls[0][1]).not.toHaveProperty('totalScore');
  });
});

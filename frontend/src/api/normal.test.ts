import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../../lib/api';
import { extractCvPdf, getCv, listMyCvs, searchCvs, searchJobs } from './normal';
import type {
  NormalCVSearchItem,
  NormalCv,
  NormalJobSearchItem,
  NormalSearchResponse,
} from '../../types';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
};

describe('normal API client', () => {
  beforeEach(() => {
    mockedApi.get.mockReset();
    mockedApi.post.mockReset();
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
});

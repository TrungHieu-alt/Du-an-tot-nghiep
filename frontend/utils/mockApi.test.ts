import { beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../lib/api';
import {
  createCv,
  createRequirement,
  deleteCv,
  deleteRequirement,
  searchCandidatesApi,
  searchJobsApi,
  sendChatMessage,
  updateCv,
  updateRequirement,
} from './mockApi';

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('mockApi utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();
    sessionStorage.setItem('user', JSON.stringify({ id: '9', email: 'dev@example.com' }));
  });

  it('searchJobsApi in matching mode calls canonical cv->jobs endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          job_id: 11,
          jd: { title: 'Backend Engineer', location: 'Hanoi', skills: ['Node.js'] },
          llm_score: 87,
          reason: 'Strong fit',
        },
      ],
    } as any);

    const result = await searchJobsApi(
      { q: '', location: '', filters: {}, sort: 'relevance', page: 1 },
      'cv-1'
    );

    expect(api.get).toHaveBeenCalledWith('/cv/match/cv-1/jobs', { params: { top_k: 20 } });
    expect(result.data[0]).toMatchObject({ id: 11, title: 'Backend Engineer' });
  });

  it('searchCandidatesApi falls back to /candidate/profiles when match endpoint fails', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('match endpoint failed'))
      .mockResolvedValueOnce({
        data: [
          {
            user_id: 2,
            full_name: 'Nguyen Van A',
            skills: ['Node.js', 'MongoDB'],
            experience_years: 3,
            location: 'HCM',
          },
        ],
      } as any);

    const result = await searchCandidatesApi(
      { q: '', location: '', filters: {}, sort: 'relevance', page: 1 },
      'job-9'
    );

    expect(vi.mocked(api.get).mock.calls[0][0]).toBe('/jobs/match/job-9/cvs');
    expect(vi.mocked(api.get).mock.calls[1][0]).toBe('/candidate/profiles');
    expect(result.data).toHaveLength(1);
    expect(result.data[0]).toMatchObject({
      id: '2',
      name: 'Nguyen Van A',
      yearsOfExperience: 3,
      experienceLevel: 'Mid-Level',
    });
  });

  it('requirement CRUD helpers call canonical jobs endpoints', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'r1', title: 'Req' } } as any);
    vi.mocked(api.put).mockResolvedValue({ data: { id: 'r1', title: 'Req updated' } } as any);
    vi.mocked(api.delete).mockResolvedValue({ status: 200 } as any);

    await createRequirement({ id: 'r1' } as any);
    await updateRequirement('r1', { title: 'Req updated' });
    const deleted = await deleteRequirement('r1');

    expect(api.post).toHaveBeenCalledWith('/jobs/create/9', { id: 'r1' });
    expect(api.put).toHaveBeenCalledWith('/jobs/r1', { title: 'Req updated' });
    expect(api.delete).toHaveBeenCalledWith('/jobs/r1');
    expect(deleted).toBe(true);
  });

  it('cv CRUD helpers call canonical cv endpoints', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 'cv1', name: 'CV 1' } } as any);
    vi.mocked(api.put).mockResolvedValue({ data: { id: 'cv1', name: 'CV 1 updated' } } as any);
    vi.mocked(api.delete).mockResolvedValue({ status: 200 } as any);

    await createCv({ id: 'cv1' } as any);
    await updateCv('cv1', { name: 'CV 1 updated' } as any);
    const deleted = await deleteCv('cv1');

    expect(api.post).toHaveBeenCalledWith('/cv/create/9', { id: 'cv1' });
    expect(api.put).toHaveBeenCalledWith('/cv/cv1', { name: 'CV 1 updated' });
    expect(api.delete).toHaveBeenCalledWith('/cv/cv1');
    expect(deleted).toBe(true);
  });

  it('sendChatMessage returns unsupported notice', async () => {
    const result = await sendChatMessage('hello');
    expect(result).toContain('chưa khả dụng');
    expect(api.post).not.toHaveBeenCalled();
  });
});

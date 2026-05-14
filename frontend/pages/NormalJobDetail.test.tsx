import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/api/normal', () => ({
  createApplication: vi.fn(),
  getJob: vi.fn(),
  listJobApplications: vi.fn(),
  listMyApplications: vi.fn(),
  listMyCvs: vi.fn(),
  updateApplicationStatus: vi.fn(),
}));

import NormalJobDetail from './NormalJobDetail';
import { useAuth } from '../contexts/AuthContext';
import {
  createApplication,
  getJob,
  listJobApplications,
  listMyApplications,
  listMyCvs,
  updateApplicationStatus,
} from '../src/api/normal';
import type { NormalApplication, NormalCv, NormalJob } from '../types';

const mockedUseAuth = vi.mocked(useAuth);
const mockedGetJob = vi.mocked(getJob);
const mockedListMyCvs = vi.mocked(listMyCvs);
const mockedCreateApplication = vi.mocked(createApplication);
const mockedListMyApplications = vi.mocked(listMyApplications);
const mockedListJobApplications = vi.mocked(listJobApplications);
const mockedUpdateApplicationStatus = vi.mocked(updateApplicationStatus);

const job = (overrides: Partial<NormalJob> = {}): NormalJob => ({
  id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  created_by: 'recruiter-1',
  title: 'Backend Engineer',
  status: 'published',
  visibility: 'public',
  company_name: 'Demo Co',
  company_industry: 'Information Technology',
  department: 'Engineering',
  location: { city: 'Hanoi' },
  employment_type: ['fulltime'],
  seniority: 'middle',
  description: 'Build APIs',
  responsibilities: [],
  requirements: ['FastAPI'],
  skills: [{ name: 'Python' }],
  salary: {},
  tags: [],
  categories: [],
  remote: false,
  archived: false,
  applications_count: 0,
  created_at: '2026-05-14T00:00:00Z',
  updated_at: '2026-05-14T00:00:00Z',
  ...overrides,
});

const cv = (overrides: Partial<NormalCv> = {}): NormalCv => ({
  id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  created_by: 'candidate-1',
  fullname: 'Nguyen Van A',
  headline: 'Backend Candidate',
  location: {},
  employment_type: ['fulltime'],
  skills: [],
  experiences: [],
  education: [],
  certifications: [],
  status: 'published',
  visibility: 'public',
  tags: [],
  file: {},
  archived: false,
  created_at: '2026-05-14T00:00:00Z',
  updated_at: '2026-05-14T00:00:00Z',
  ...overrides,
});

const application = (overrides: Partial<NormalApplication> = {}): NormalApplication => ({
  id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
  jobId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  cvId: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
  candidateId: 'candidate-1',
  recruiterId: 'recruiter-1',
  status: 'submitted',
  coverLetter: 'I can start next month.',
  createdAt: '2026-05-14T00:00:00Z',
  updatedAt: '2026-05-14T00:00:00Z',
  job: { id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', title: 'Backend Engineer', companyName: 'Demo Co' },
  cv: { id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', fullname: 'Nguyen Van A', headline: 'Backend Candidate' },
  candidate: { id: 'candidate-1', email: 'candidate@example.com', fullName: 'Nguyen Van A', role: 'candidate' },
  ...overrides,
});

const candidateAuth = {
  accessToken: 'candidate-token',
  user: {
    id: 'candidate-1',
    email: 'candidate@example.com',
    full_name: 'Nguyen Van A',
    role: 'candidate' as const,
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  googleLogin: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshMe: vi.fn(),
};

const recruiterAuth = {
  ...candidateAuth,
  accessToken: 'recruiter-token',
  user: {
    id: 'recruiter-1',
    email: 'recruiter@example.com',
    full_name: 'Demo Recruiter',
    role: 'employer' as const,
  },
};

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/job/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa']}>
      <Routes>
        <Route path="/job/:id" element={<NormalJobDetail />} />
      </Routes>
    </MemoryRouter>
  );

describe('NormalJobDetail application flow', () => {
  beforeEach(() => {
    mockedUseAuth.mockReturnValue(candidateAuth);
    mockedGetJob.mockReset();
    mockedListMyCvs.mockReset();
    mockedCreateApplication.mockReset();
    mockedListMyApplications.mockReset();
    mockedListJobApplications.mockReset();
    mockedUpdateApplicationStatus.mockReset();
    mockedGetJob.mockResolvedValue(job());
    mockedListMyApplications.mockResolvedValue({ items: [], total: 0, page: 1, limit: 50, totalPages: 0 });
    mockedListMyCvs.mockResolvedValue([cv()]);
    mockedCreateApplication.mockResolvedValue(application());
    mockedListJobApplications.mockResolvedValue({ items: [application()], total: 1, page: 1, limit: 50, totalPages: 1 });
    mockedUpdateApplicationStatus.mockResolvedValue(application({ status: 'reviewing' }));
  });

  it('shows Apply with CV for candidates and submits jobId plus cvId', async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByRole('heading', { name: /backend engineer/i })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /apply with cv/i }));
    expect(await screen.findByRole('radio', { name: /nguyen van a/i })).toBeChecked();
    await user.type(screen.getByLabelText(/cover letter/i), 'Hello recruiter');
    await user.click(screen.getByRole('button', { name: /submit application/i }));

    expect(mockedListMyCvs).toHaveBeenCalledWith('candidate-token');
    expect(mockedCreateApplication).toHaveBeenCalledWith('candidate-token', {
      jobId: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      cvId: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      coverLetter: 'Hello recruiter',
    });
    expect(mockedCreateApplication.mock.calls[0][1]).not.toHaveProperty('matchScore');
    expect(screen.queryByText(/totalScore|matchLevel|recommendation/i)).not.toBeInTheDocument();
  });

  it('shows application errors for duplicate or failed submissions', async () => {
    mockedCreateApplication.mockRejectedValueOnce({
      response: { data: { detail: 'Application already exists for this job' } },
    });
    const user = userEvent.setup();
    renderPage();

    await screen.findByRole('heading', { name: /backend engineer/i });
    await user.click(screen.getByRole('button', { name: /apply with cv/i }));
    await user.click(await screen.findByRole('button', { name: /submit application/i }));

    expect(await screen.findByText(/application already exists/i)).toBeInTheDocument();
  });

  it('lets recruiters load applicants and update status without matching scores', async () => {
    mockedUseAuth.mockReturnValue(recruiterAuth);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByRole('heading', { name: /backend engineer/i })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /view applicants/i }));
    expect(await screen.findByText('Nguyen Van A')).toBeInTheDocument();

    await user.selectOptions(
      screen.getByLabelText(/application status for nguyen van a/i),
      'reviewing'
    );

    expect(mockedListJobApplications).toHaveBeenCalledWith(
      'recruiter-token',
      'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      { limit: 50 }
    );
    expect(mockedUpdateApplicationStatus).toHaveBeenCalledWith(
      'recruiter-token',
      'cccccccc-cccc-cccc-cccc-cccccccccccc',
      'reviewing'
    );
    expect(screen.queryByText(/matchScore|recommendation|strengths|weaknesses/i)).not.toBeInTheDocument();
  });
});

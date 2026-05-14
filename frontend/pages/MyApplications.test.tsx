import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/api/normal', () => ({
  listMyApplications: vi.fn(),
}));

import MyApplications from './MyApplications';
import { useAuth } from '../contexts/AuthContext';
import { listMyApplications } from '../src/api/normal';
import type { NormalApplication } from '../types';

const mockedUseAuth = vi.mocked(useAuth);
const mockedListMyApplications = vi.mocked(listMyApplications);

const authValue = {
  accessToken: 'token',
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

const application = (overrides: Partial<NormalApplication> = {}): NormalApplication => ({
  id: 'app-1',
  jobId: 'job-1',
  cvId: 'cv-1',
  candidateId: 'candidate-1',
  recruiterId: 'recruiter-1',
  status: 'submitted',
  coverLetter: 'Short cover letter',
  createdAt: '2026-05-14T00:00:00Z',
  updatedAt: '2026-05-14T00:00:00Z',
  job: { id: 'job-1', title: 'Backend Engineer', companyName: 'Demo Co' },
  cv: { id: 'cv-1', fullname: 'Nguyen Van A', headline: 'Backend Candidate' },
  ...overrides,
});

const renderPage = () =>
  render(
    <MemoryRouter>
      <MyApplications />
    </MemoryRouter>
  );

describe('MyApplications page', () => {
  beforeEach(() => {
    mockedUseAuth.mockReturnValue(authValue);
    mockedListMyApplications.mockReset();
    mockedListMyApplications.mockResolvedValue({
      items: [application()],
      total: 1,
      page: 1,
      limit: 50,
      totalPages: 1,
    });
  });

  it('renders submitted applications without score or matching fields', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: /my applications/i })).toBeInTheDocument();
    expect(mockedListMyApplications).toHaveBeenCalledWith('token', { limit: 50 });
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument();
    expect(screen.getByText(/cv: nguyen van a/i)).toBeInTheDocument();
    expect(screen.getByText('submitted')).toBeInTheDocument();
    expect(screen.queryByText(/matchScore|totalScore|recommendation/i)).not.toBeInTheDocument();
  });
});

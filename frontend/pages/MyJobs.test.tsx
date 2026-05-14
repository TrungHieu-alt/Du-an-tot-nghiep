import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/api/normal', () => ({
  createJob: vi.fn(),
  deleteJob: vi.fn(),
  listMyJobs: vi.fn(),
  updateJob: vi.fn(),
}));

import MyJobs from './MyJobs';
import { useAuth } from '../contexts/AuthContext';
import { createJob, listMyJobs, updateJob } from '../src/api/normal';
import type { NormalJob } from '../types';

const mockedUseAuth = vi.mocked(useAuth);
const mockedListMyJobs = vi.mocked(listMyJobs);
const mockedUpdateJob = vi.mocked(updateJob);
const mockedCreateJob = vi.mocked(createJob);

const authValue = {
  accessToken: 'token',
  user: {
    id: 'user-1',
    email: 'recruiter@example.com',
    full_name: 'Demo Recruiter',
    role: 'employer' as const,
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  googleLogin: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshMe: vi.fn(),
};

const job = (overrides: Partial<NormalJob> = {}): NormalJob => ({
  id: 'job-1',
  created_by: 'user-1',
  title: 'Marketing Executive',
  status: 'published',
  visibility: 'public',
  company_name: 'Demo Co',
  company_industry: 'Marketing',
  department: 'Growth',
  location: { city: 'Hanoi' },
  employment_type: ['fulltime'],
  seniority: 'junior',
  description: 'Run campaigns',
  responsibilities: [],
  requirements: [],
  skills: [{ name: 'Communication' }],
  salary: {},
  tags: [],
  categories: [],
  remote: false,
  archived: false,
  applications_count: 3,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
  ...overrides,
});

const PathProbe = () => {
  const location = useLocation();
  return <span data-testid="path">{location.pathname}</span>;
};

const renderPage = (initialPath = '/employer/requests') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <MyJobs />
      <PathProbe />
    </MemoryRouter>
  );

describe('MyJobs card grid management', () => {
  beforeEach(() => {
    mockedUseAuth.mockReturnValue(authValue);
    mockedListMyJobs.mockReset();
    mockedUpdateJob.mockReset();
    mockedCreateJob.mockReset();
    mockedUpdateJob.mockResolvedValue(job());
    mockedCreateJob.mockResolvedValue(job());
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('renders recruitment requirements as cards and keeps the plus card visible', async () => {
    mockedListMyJobs.mockResolvedValue([
      job(),
      job({
        id: 'job-2',
        title: 'Accountant',
        company_name: 'Finance Co',
        company_industry: 'Accounting',
        visibility: 'private',
        applications_count: 1,
      }),
    ]);

    renderPage();

    expect(await screen.findByRole('heading', { name: /yêu cầu tuyển dụng của tôi/i })).toBeInTheDocument();
    expect(mockedListMyJobs).toHaveBeenCalledWith('token');
    expect(screen.getByLabelText('Tạo yêu cầu tuyển dụng mới')).toBeInTheDocument();
    expect(screen.getByText('Marketing Executive')).toBeInTheDocument();
    expect(screen.getByText('Accountant')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /chỉnh sửa/i })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: /đóng tuyển/i })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: /xóa/i })).toHaveLength(2);
  });

  it('navigates from plus card and existing job card without using V2 routes', async () => {
    mockedListMyJobs.mockResolvedValue([job()]);
    const user = userEvent.setup();

    const firstRender = renderPage();

    await screen.findByText('Marketing Executive');
    await user.click(screen.getByLabelText('Tạo yêu cầu tuyển dụng mới'));
    expect(screen.getByTestId('path')).toHaveTextContent('/employer/requests/new');

    firstRender.unmount();
    renderPage();
    await screen.findByText('Marketing Executive');
    await user.click(screen.getByRole('link', { name: /mở yêu cầu tuyển dụng marketing executive/i }));
    expect(screen.getByTestId('path')).toHaveTextContent('/employer/requests/job-1');
  });

  it('keeps action button clicks from navigating the card', async () => {
    mockedListMyJobs.mockResolvedValue([job()]);
    const user = userEvent.setup();

    renderPage();

    await screen.findByText('Marketing Executive');
    await user.click(screen.getByRole('button', { name: /ẩn/i }));

    expect(mockedUpdateJob).toHaveBeenCalledWith('token', 'job-1', {
      status: 'published',
      visibility: 'private',
      archived: false,
    });
    expect(screen.getByTestId('path')).toHaveTextContent('/employer/requests');
  });

  it('shows an empty state while still rendering the plus card', async () => {
    mockedListMyJobs.mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText(/bạn chưa có yêu cầu tuyển dụng nào/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Tạo yêu cầu tuyển dụng mới')).toBeInTheDocument();
  });

  it('creates jobs with normalized enum keys from the form defaults', async () => {
    mockedListMyJobs.mockResolvedValue([]);
    const user = userEvent.setup();

    renderPage('/employer/requests/new');

    expect(screen.getByText(/step 1 of 7/i)).toBeInTheDocument();
    expect(screen.getAllByText(/basic job information/i).length).toBeGreaterThan(0);

    await user.type(screen.getByLabelText(/job title/i), 'Accountant');
    await user.type(screen.getByLabelText(/^company name/i), 'Finance Co');
    await user.click(screen.getByRole('button', { name: /save draft/i }));

    expect(mockedCreateJob).toHaveBeenCalledWith('token', expect.objectContaining({
      title: 'Accountant',
      company_name: 'Finance Co',
      industry: 'unknown',
      occupation_group: 'unknown',
      seniority: 'unknown',
      employment_type: ['fulltime'],
      status: 'draft',
      visibility: 'private',
      education_level: 'unknown',
      salary: expect.objectContaining({
        currency: 'VND',
        period: 'month',
      }),
    }));
    expect(mockedCreateJob.mock.calls[0][1]).not.toHaveProperty('matchScore');
    expect(mockedCreateJob.mock.calls[0][1]).not.toHaveProperty('matchLevel');
    expect(mockedCreateJob.mock.calls[0][1]).not.toHaveProperty('recommendation');
  });
});

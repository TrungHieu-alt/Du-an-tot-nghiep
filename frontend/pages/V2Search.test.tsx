import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../src/api/normal', () => ({
  searchJobs: vi.fn(),
  searchCvs: vi.fn(),
}));

import V2Search from './V2Search';
import { searchCvs, searchJobs } from '../src/api/normal';
import { AuthProvider } from '../contexts/AuthContext';
import type {
  NormalCVSearchItem,
  NormalJobSearchItem,
  NormalSearchResponse,
} from '../types';

const mockedSearchJobs = vi.mocked(searchJobs);
const mockedSearchCvs = vi.mocked(searchCvs);

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/v2/search" element={<AuthProvider><V2Search /></AuthProvider>} />
        <Route path="/jobs/search" element={<AuthProvider><V2Search /></AuthProvider>} />
        <Route path="/cvs/search" element={<AuthProvider><V2Search /></AuthProvider>} />
      </Routes>
    </MemoryRouter>
  );

const buildJobs = (count: number): NormalJobSearchItem[] =>
  Array.from({ length: count }, (_, i) => ({
    job_id: String(4001 + i),
    id: String(4001 + i),
    title: `Job ${i + 1}`,
    location: 'ha_noi',
    job_type: 'remote',
    seniority: 'senior',
    education: 'dai_hoc',
    skills: ['python'],
    requirement: 'General job requirement',
    employment_type: ['remote'],
    working_model: 'remote',
  }));

const buildCvs = (count: number): NormalCVSearchItem[] =>
  Array.from({ length: count }, (_, i) => ({
    cv_id: String(5001 + i),
    id: String(5001 + i),
    title: `Candidate ${i + 1}`,
    fullname: `Candidate ${i + 1}`,
    location: 'tp_hcm',
    job_type: 'fulltime',
    seniority: 'junior',
    education: 'dai_hoc',
    skills: ['react'],
    summary: 'Public candidate summary',
    experience: 'Built normal frontend apps',
    certifications: [],
    employment_type: ['fulltime'],
    working_model: 'hybrid',
  }));

describe('V2Search page', () => {
  beforeEach(() => {
    mockedSearchJobs.mockReset();
    mockedSearchCvs.mockReset();
  });

  it('loads public jobs when q and filters are empty in job mode', async () => {
    mockedSearchJobs.mockResolvedValueOnce({
      items: buildJobs(1),
      total: 1,
      page: 1,
      limit: 10,
      totalPages: 1,
    });

    renderAt('/jobs/search');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith({
        q: undefined,
        location: undefined,
        industry: undefined,
        employmentType: undefined,
        experienceLevel: undefined,
        salaryMin: undefined,
        salaryMax: undefined,
        educationLevel: undefined,
        workingModel: undefined,
        skills: undefined,
        page: 1,
        limit: 10,
        sort: 'newest',
      });
    });
    expect(await screen.findByText('Job 1')).toBeInTheDocument();
  });

  it('loads public CVs when q and filters are empty in cv mode', async () => {
    mockedSearchCvs.mockResolvedValueOnce({
      items: buildCvs(1),
      total: 1,
      page: 1,
      limit: 10,
      totalPages: 1,
    });

    renderAt('/cvs/search');

    expect(mockedSearchJobs).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenCalledWith({
        q: undefined,
        location: undefined,
        desiredIndustry: undefined,
        experienceLevel: undefined,
        yearsOfExperience: undefined,
        educationLevel: undefined,
        expectedSalaryMin: undefined,
        expectedSalaryMax: undefined,
        workingModel: undefined,
        availability: undefined,
        skills: undefined,
        page: 1,
        limit: 10,
        sort: 'newest',
      });
    });
    expect(await screen.findByText('Candidate 1')).toBeInTheDocument();
  });

  it('searches jobs with URL params and renders cards without percentages', async () => {
    const payload: NormalSearchResponse<NormalJobSearchItem> = {
      items: buildJobs(3),
      total: 3,
      page: 1,
      limit: 10,
      totalPages: 1,
    };
    mockedSearchJobs.mockResolvedValueOnce(payload);

    renderAt('/v2/search?q=marketing&type=job');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith({
        q: 'marketing',
        location: undefined,
        industry: undefined,
        employmentType: undefined,
        experienceLevel: undefined,
        salaryMin: undefined,
        salaryMax: undefined,
        educationLevel: undefined,
        workingModel: undefined,
        skills: undefined,
        page: 1,
        limit: 10,
        sort: 'newest',
      });
    });
    expect(await screen.findByText('Job 1')).toBeInTheDocument();
    expect(screen.queryByText(/match/i)).not.toBeInTheDocument();
    expect(screen.getByText(/Tìm thấy/i)).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('forwards general job filters to the normal search API', async () => {
    mockedSearchJobs.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });
    renderAt(
      '/v2/search?q=x&type=job&location=ha_noi&industry=marketing&employmentType=fulltime&experienceLevel=junior&educationLevel=bachelor&workingModel=onsite&skills=excel&sort=most_relevant'
    );

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith({
        q: 'x',
        location: 'ha_noi',
        industry: 'marketing',
        employmentType: 'fulltime',
        experienceLevel: 'junior',
        salaryMin: undefined,
        salaryMax: undefined,
        educationLevel: 'bachelor',
        workingModel: 'onsite',
        skills: 'excel',
        page: 1,
        limit: 10,
        sort: 'most_relevant',
      });
    });
  });

  it('switches to CV search when toggle is clicked', async () => {
    mockedSearchJobs.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });
    const cvPayload: NormalSearchResponse<NormalCVSearchItem> = {
      items: [
        {
          cv_id: '3001',
          id: '3001',
          title: 'Marketing Candidate',
          location: 'tp_hcm',
          job_type: 'fulltime',
          seniority: 'mid',
          education: 'dai_hoc',
          skills: ['content'],
          summary: 'Marketing summary',
          experience: '3 years',
          certifications: [],
          employment_type: ['fulltime'],
          working_model: 'onsite',
        },
      ],
      total: 1,
      page: 1,
      limit: 10,
      totalPages: 1,
    };
    mockedSearchCvs.mockResolvedValueOnce(cvPayload);

    renderAt('/v2/search?q=marketing&type=job');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalled();
    });

    await userEvent.click(screen.getByRole('button', { name: /Tìm CV/i }));

    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenCalledWith({
        q: 'marketing',
        location: undefined,
        desiredIndustry: undefined,
        experienceLevel: undefined,
        yearsOfExperience: undefined,
        educationLevel: undefined,
        expectedSalaryMin: undefined,
        expectedSalaryMax: undefined,
        workingModel: undefined,
        availability: undefined,
        skills: undefined,
        page: 1,
        limit: 10,
        sort: 'newest',
      });
    });
    expect(await screen.findByText('Marketing Candidate')).toBeInTheDocument();
  });

  it('shows the empty-state message when total is 0', async () => {
    mockedSearchJobs.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });
    renderAt('/v2/search?q=logistics&type=job');

    expect(await screen.findByText(/No published public jobs found/i)).toBeInTheDocument();
  });

  it('renders pagination when the backend reports multiple pages', async () => {
    mockedSearchJobs.mockResolvedValueOnce({
      items: buildJobs(2),
      total: 12,
      page: 1,
      limit: 10,
      totalPages: 2,
    });
    renderAt('/v2/search?q=sales&type=job');

    expect(await screen.findByText('Trang 1 / 2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sau/i })).toBeInTheDocument();
  });
});

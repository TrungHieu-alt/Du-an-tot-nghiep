import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
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
    employment_type: ['fulltime'],
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
    mockedSearchJobs.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });
    mockedSearchCvs.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 10,
      totalPages: 0,
    });
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
      expect(mockedSearchJobs).toHaveBeenCalledWith(expect.objectContaining({
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
        sort: 'createdAt_desc',
      }));
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
      expect(mockedSearchCvs).toHaveBeenCalledWith(expect.objectContaining({
        q: undefined,
        location: undefined,
        locationCountry: undefined,
        desiredIndustry: undefined,
        careerLevel: undefined,
        yearsOfExperienceMin: undefined,
        yearsOfExperienceMax: undefined,
        educationLevel: undefined,
        educationMajor: undefined,
        workingModel: undefined,
        employmentType: undefined,
        availability: undefined,
        skills: undefined,
        toolsAndTechnologies: undefined,
        domainKnowledge: undefined,
        certificationName: undefined,
        languageName: undefined,
        languageLevel: undefined,
        status: undefined,
        tags: undefined,
        page: 1,
        limit: 10,
        sort: 'createdAt_desc',
      }));
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
      expect(mockedSearchJobs).toHaveBeenCalledWith(expect.objectContaining({
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
        sort: 'createdAt_desc',
      }));
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
      '/v2/search?q=x&type=job&location=ha_noi&industry=marketing&employmentType=fulltime&experienceLevel=junior&educationLevel=bachelor&workingModel=onsite&skills=excel&sort=createdAt_desc'
    );

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith(expect.objectContaining({
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
        sort: 'createdAt_desc',
      }));
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
          seniority: 'middle',
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
      expect(mockedSearchCvs).toHaveBeenCalledWith(expect.objectContaining({
        q: 'marketing',
        location: undefined,
        desiredIndustry: undefined,
        careerLevel: undefined,
        yearsOfExperienceMin: undefined,
        yearsOfExperienceMax: undefined,
        educationLevel: undefined,
        workingModel: undefined,
        availability: undefined,
        skills: undefined,
        page: 1,
        limit: 10,
        sort: 'createdAt_desc',
      }));
    });
    expect(await screen.findByText('Marketing Candidate')).toBeInTheDocument();
  });

  it('sends normalized multi-industry CV filters from the panel', async () => {
    const user = userEvent.setup();
    renderAt('/cvs/search?type=cv');

    await waitFor(() => expect(mockedSearchCvs).toHaveBeenCalled());

    await user.selectOptions(screen.getByLabelText(/^industry$/i), 'information_technology');
    await user.selectOptions(screen.getByLabelText(/occupation group/i), 'software_engineering');
    await user.click(screen.getByRole('button', { name: /^Junior$/i }));
    await user.click(screen.getByRole('button', { name: /^Middle$/i }));
    await user.click(screen.getByRole('button', { name: /^Full-time$/i }));
    await user.type(screen.getByLabelText(/years min/i), '1');
    await user.type(screen.getByLabelText(/years max/i), '4');
    await user.type(screen.getByLabelText(/^city$/i), 'Hà Nội');
    await user.type(screen.getByLabelText(/^country$/i), 'Việt Nam');
    await user.type(screen.getByLabelText(/^skills/i), 'ReactJS, Postgres, MS Excel');
    await user.type(screen.getByLabelText(/tools and technologies/i), 'FastAPI');
    await user.type(screen.getByLabelText(/domain knowledge/i), 'ecommerce');
    await user.click(screen.getByRole('button', { name: /^Bachelor$/i }));
    await user.type(screen.getByLabelText(/education major/i), 'Computer Science');
    await user.type(screen.getByLabelText(/certifications/i), 'AWS');
    await user.type(screen.getByLabelText(/language name/i), 'English');
    await user.selectOptions(screen.getByLabelText(/language level/i), 'intermediate');
    await user.type(screen.getByLabelText(/^tags/i), 'backend');
    await user.selectOptions(screen.getByLabelText(/sort results/i), 'yearsOfExperience_desc');
    await user.click(screen.getByRole('button', { name: /apply filters/i }));

    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenLastCalledWith(expect.objectContaining({
        desiredIndustry: 'information_technology',
        occupationGroup: 'software_engineering',
        careerLevel: 'junior,middle',
        yearsOfExperienceMin: 1,
        yearsOfExperienceMax: 4,
        employmentType: 'fulltime',
        location: 'Hà Nội',
        locationCountry: 'Việt Nam',
        skills: 'react,postgresql,excel',
        toolsAndTechnologies: 'fastapi',
        domainKnowledge: 'ecommerce',
        educationLevel: 'bachelor',
        educationMajor: 'Computer Science',
        certificationName: 'aws',
        languageName: 'English',
        languageLevel: 'intermediate',
        tags: 'backend',
        sort: 'yearsOfExperience_desc',
      }));
    });
  });

  it('scopes occupation group options by selected industry', async () => {
    const user = userEvent.setup();
    renderAt('/cvs/search?type=cv');

    await user.selectOptions(await screen.findByLabelText(/^industry$/i), 'accounting_finance');
    const occupationSelect = screen.getByLabelText(/occupation group/i);

    expect(within(occupationSelect).getByRole('option', { name: /^Accountant$/i })).toBeInTheDocument();
    expect(within(occupationSelect).queryByRole('option', { name: /Software Engineering/i })).not.toBeInTheDocument();
  });

  it('clears active CV filters and removes filter chips', async () => {
    const user = userEvent.setup();
    renderAt('/cvs/search?type=cv&industry=sales&careerLevel=junior,middle&skills=react');

    expect(await screen.findByText(/Industry: Sales/i)).toBeInTheDocument();
    expect(screen.getByText(/Skill: react/i)).toBeInTheDocument();

    await user.click(screen.getAllByRole('button', { name: /^Clear$/i })[0]);

    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenLastCalledWith(expect.objectContaining({
        desiredIndustry: undefined,
        careerLevel: undefined,
        skills: undefined,
      }));
    });
    expect(screen.queryByText(/Industry: Sales/i)).not.toBeInTheDocument();
  });

  it('removes one active CV filter chip without clearing the other filters', async () => {
    const user = userEvent.setup();
    renderAt('/cvs/search?type=cv&industry=sales&careerLevel=junior,middle&skills=react');

    expect(await screen.findByRole('button', { name: /Skill: react/i })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Skill: react/i }));

    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenLastCalledWith(expect.objectContaining({
        desiredIndustry: 'sales',
        careerLevel: 'junior,middle',
        skills: undefined,
      }));
    });
    expect(screen.getByText(/Industry: Sales/i)).toBeInTheDocument();
    expect(screen.queryByText(/Skill: react/i)).not.toBeInTheDocument();
  });

  it('does not forward matching or scoring fields in normal CV search requests', async () => {
    renderAt('/cvs/search?type=cv&q=react&matchScore=99&matchLevel=top&totalScore=99&recommendation=review');

    await waitFor(() => expect(mockedSearchCvs).toHaveBeenCalled());

    const lastCall = mockedSearchCvs.mock.calls[mockedSearchCvs.mock.calls.length - 1];
    const request = lastCall[0] as Record<string, unknown>;
    [
      'totalScore',
      'matchScore',
      'matchLevel',
      'scores',
      'strengths',
      'weaknesses',
      'recommendation',
      'matchedSkills',
      'missingMustHaveSkills',
      'missingNiceToHaveSkills',
    ].forEach((field) => {
      expect(request).not.toHaveProperty(field);
    });
  });

  it('does not render score or recommendation fields in normal CV results', async () => {
    mockedSearchCvs.mockResolvedValueOnce({
      items: [
        {
          ...buildCvs(1)[0],
          totalScore: 99,
          matchScore: 99,
          matchLevel: 'excellent_match',
          strengths: ['Score strength text'],
          weaknesses: ['Score weakness text'],
          recommendation: 'Review as top match',
        } as NormalCVSearchItem,
      ],
      total: 1,
      page: 1,
      limit: 10,
      totalPages: 1,
    });

    renderAt('/cvs/search?type=cv&q=react');

    expect(await screen.findByText('Candidate 1')).toBeInTheDocument();
    expect(screen.queryByText(/excellent_match/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Review as top match/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Score strength text/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Score weakness text/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/99/)).not.toBeInTheDocument();
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

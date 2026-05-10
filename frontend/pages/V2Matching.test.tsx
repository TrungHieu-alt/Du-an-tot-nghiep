import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../src/api/v2', () => ({
  listV2Jobs: vi.fn(),
  listV2Cvs: vi.fn(),
  getV2Job: vi.fn(),
  getV2Cv: vi.fn(),
  runV2MatchForJob: vi.fn(),
  runV2MatchForCv: vi.fn(),
}));

import V2Matching from './V2Matching';
import {
  getV2Cv,
  getV2Job,
  listV2Cvs,
  listV2Jobs,
  runV2MatchForCv,
  runV2MatchForJob,
} from '../src/api/v2';
import type { CVV2Detail, JobV2Detail, RunMatchingV2Response } from '../types';

const mockedListJobs = vi.mocked(listV2Jobs);
const mockedListCvs = vi.mocked(listV2Cvs);
const mockedGetJob = vi.mocked(getV2Job);
const mockedGetCv = vi.mocked(getV2Cv);
const mockedRunForJob = vi.mocked(runV2MatchForJob);
const mockedRunForCv = vi.mocked(runV2MatchForCv);

const sampleJobs = [
  {
    job_id: 4001,
    title: 'Senior Backend',
    location: 'ha_noi' as const,
    job_type: 'remote' as const,
    seniority: 'senior' as const,
    skills: ['python'],
  },
  {
    job_id: 4002,
    title: 'Lead Frontend',
    location: 'ha_noi' as const,
    job_type: 'fulltime' as const,
    seniority: 'lead' as const,
    skills: ['react'],
  },
];

const jobDetail: JobV2Detail = {
  job_id: 4001,
  title: 'Senior Backend',
  skills: ['python', 'docker'],
  requirement: '3+ năm',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  education: 'dai_hoc',
  required_certifications: [],
};

const buildResponse = (matchCount: number): RunMatchingV2Response => ({
  anchor_type: 'job',
  anchor_id: 4001,
  total_candidates: 36,
  total_after_filter: 12,
  total_returned: matchCount,
  runtime_ms_total: 22.5,
  runtime_ms_filter: 1.2,
  runtime_ms_scoring: 18.0,
  runtime_ms_sort: 0.3,
  matches: Array.from({ length: matchCount }, (_, i) => ({
    rank: i + 1,
    cv_id: 3001 + i,
    job_id: 4001,
    final_score: 0.95 - i * 0.05,
    title_score: 0.9,
    skills_score: 0.95,
    req_exp_score: 0.85,
    req_summary_score: 0.8,
    reasoning: `match #${i + 1}`,
  })),
});

const renderPage = (initialPath = '/v2/matching') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <V2Matching />
    </MemoryRouter>
  );

const cvDetail: CVV2Detail = {
  cv_id: 3001,
  title: 'Senior Backend',
  skills: ['python'],
  summary: '',
  experience: '',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  education: 'dai_hoc',
  certifications: [],
};

describe('V2Matching page', () => {
  beforeEach(() => {
    mockedListJobs.mockReset();
    mockedListCvs.mockReset();
    mockedGetJob.mockReset();
    mockedGetCv.mockReset();
    mockedRunForJob.mockReset();
    mockedRunForCv.mockReset();
  });

  it('runs the full flow: select job → set top_k=5 → click Run → render N cards', async () => {
    mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
    mockedListCvs.mockResolvedValue({ items: [], total: 0 });
    mockedGetJob.mockResolvedValueOnce(jobDetail);
    mockedRunForJob.mockResolvedValueOnce(buildResponse(5));

    renderPage();

    // Pick a job from the left column
    const jobItem = await screen.findByText('Senior Backend');
    await userEvent.click(jobItem);

    // Anchor preview shows the job
    await waitFor(() => {
      expect(mockedGetJob).toHaveBeenCalledWith(4001);
    });
    expect(await screen.findByText('docker')).toBeInTheDocument();

    // Slider for top_k — set to 5
    const sliders = screen.getAllByRole('slider');
    expect(sliders.length).toBeGreaterThanOrEqual(2);
    const topKSlider = sliders[0] as HTMLInputElement;
    expect(topKSlider.max).toBe('10');
    expect(topKSlider.min).toBe('1');
    // fireEvent.change properly triggers React's onChange on range inputs
    fireEvent.change(topKSlider, { target: { value: '5' } });

    // Click Run
    const runBtn = screen.getByRole('button', { name: /Run Matching V2/i });
    await userEvent.click(runBtn);

    // Backend invoked with the configured params
    await waitFor(() => {
      expect(mockedRunForJob).toHaveBeenCalledWith(4001, {
        top_k: 5,
        min_score: 0.7,
      });
    });

    // Stats banner — disambiguate by scoping to the stat pill that contains
    // the matching label, since `5` would also appear as a rank badge.
    expect(await screen.findByText('36')).toBeInTheDocument();   // total_candidates (unique)
    expect(screen.getByText('12')).toBeInTheDocument();          // total_after_filter (unique)
    const returnedPill = screen.getByText('Returned').parentElement!;
    expect(returnedPill.textContent).toContain('5');             // total_returned scoped

    // Cards: rank badges 1..5 confirm we rendered exactly 5 cards
    for (let i = 1; i <= 5; i += 1) {
      expect(screen.getByLabelText(`Rank ${i}`)).toBeInTheDocument();
    }
    expect(screen.queryByLabelText('Rank 6')).not.toBeInTheDocument();
  });

  it('renders the empty state when total_returned is 0', async () => {
    mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
    mockedListCvs.mockResolvedValue({ items: [], total: 0 });
    mockedGetJob.mockResolvedValue(jobDetail);
    mockedRunForJob.mockResolvedValueOnce(buildResponse(0));

    renderPage();

    await userEvent.click(await screen.findByText('Senior Backend'));
    await userEvent.click(await screen.findByRole('button', { name: /Run Matching V2/i }));

    expect(await screen.findByText(/No matches above min_score/i)).toBeInTheDocument();
  });

  it('disables the Run button until an anchor is selected', async () => {
    mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
    mockedListCvs.mockResolvedValue({ items: [], total: 0 });

    renderPage();

    const runBtn = await screen.findByRole('button', { name: /Run Matching V2/i });
    expect(runBtn).toBeDisabled();
    expect(mockedRunForJob).not.toHaveBeenCalled();
    expect(mockedRunForCv).not.toHaveBeenCalled();
  });

  // ---------------- Deep-link hydration ----------------

  describe('deep-link hydration', () => {
    it('pre-selects job anchor from ?anchor=job&id=4001 and fetches detail', async () => {
      mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
      mockedListCvs.mockResolvedValue({ items: [], total: 0 });
      mockedGetJob.mockResolvedValueOnce(jobDetail);

      renderPage('/v2/matching?anchor=job&id=4001');

      await waitFor(() => {
        expect(mockedGetJob).toHaveBeenCalledWith(4001);
      });
      // Anchor preview rendered with the fetched detail
      expect(await screen.findByText('docker')).toBeInTheDocument();
    });

    it('pre-selects cv anchor from ?anchor=cv&id=3001 and switches to cv tab', async () => {
      mockedListJobs.mockResolvedValue({ items: [], total: 0 });
      mockedListCvs.mockResolvedValue({ items: [], total: 0 });
      mockedGetCv.mockResolvedValueOnce(cvDetail);

      renderPage('/v2/matching?anchor=cv&id=3001');

      await waitFor(() => {
        expect(mockedGetCv).toHaveBeenCalledWith(3001);
      });
      expect(mockedGetJob).not.toHaveBeenCalled();
    });

    it('ignores invalid id (non-numeric) and falls back to default state', async () => {
      mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
      mockedListCvs.mockResolvedValue({ items: [], total: 0 });

      renderPage('/v2/matching?anchor=job&id=abc');

      // Wait for any async effects to settle, then assert no detail fetch.
      await waitFor(() => {
        expect(mockedListJobs).toHaveBeenCalled();
      });
      expect(mockedGetJob).not.toHaveBeenCalled();
      expect(mockedGetCv).not.toHaveBeenCalled();
    });

    it('ignores unknown anchor value', async () => {
      mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
      mockedListCvs.mockResolvedValue({ items: [], total: 0 });

      renderPage('/v2/matching?anchor=foo&id=4001');

      await waitFor(() => {
        expect(mockedListJobs).toHaveBeenCalled();
      });
      expect(mockedGetJob).not.toHaveBeenCalled();
      expect(mockedGetCv).not.toHaveBeenCalled();
    });

    it('ignores zero / negative ids', async () => {
      mockedListJobs.mockResolvedValue({ items: sampleJobs, total: 2 });
      mockedListCvs.mockResolvedValue({ items: [], total: 0 });

      renderPage('/v2/matching?anchor=job&id=0');

      await waitFor(() => {
        expect(mockedListJobs).toHaveBeenCalled();
      });
      expect(mockedGetJob).not.toHaveBeenCalled();
    });
  });
});

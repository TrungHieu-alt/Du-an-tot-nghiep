import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../src/api/v2', () => ({
  searchV2Jobs: vi.fn(),
  searchV2Cvs: vi.fn(),
}));

import V2Search from './V2Search';
import { searchV2Cvs, searchV2Jobs } from '../src/api/v2';
import type {
  CVSearchResponse,
  JobSearchItem,
  JobSearchResponse,
} from '../types';

const mockedSearchJobs = vi.mocked(searchV2Jobs);
const mockedSearchCvs = vi.mocked(searchV2Cvs);

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/v2/search" element={<V2Search />} />
      </Routes>
    </MemoryRouter>
  );

const buildJobs = (count: number, scoreFrom = 0.9): JobSearchItem[] =>
  Array.from({ length: count }, (_, i) => ({
    job_id: 4001 + i,
    title: `Job ${i + 1}`,
    location: 'ha_noi' as const,
    job_type: 'remote' as const,
    seniority: 'senior' as const,
    skills: ['python'],
    score: scoreFrom - i * 0.05,
  }));

describe('V2Search page', () => {
  beforeEach(() => {
    mockedSearchJobs.mockReset();
    mockedSearchCvs.mockReset();
  });

  it('does not call the API when q is empty', () => {
    renderAt('/v2/search');
    expect(mockedSearchJobs).not.toHaveBeenCalled();
    expect(mockedSearchCvs).not.toHaveBeenCalled();
    expect(screen.getByText(/Nhập từ khóa để bắt đầu/i)).toBeInTheDocument();
  });

  it('searches jobs with URL params and renders cards', async () => {
    const payload: JobSearchResponse = {
      items: buildJobs(3, 0.9),
      total: 3,
    };
    mockedSearchJobs.mockResolvedValueOnce(payload);

    renderAt('/v2/search?q=backend&type=job');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith({
        q: 'backend',
        top_k: 20,
        location: undefined,
        job_type: undefined,
        seniority: undefined,
      });
    });
    expect(await screen.findByText('Job 1')).toBeInTheDocument();
    expect(screen.getByText('Job 2')).toBeInTheDocument();
    expect(screen.getByText('Job 3')).toBeInTheDocument();
    expect(screen.getByText(/Tìm thấy/i)).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('forwards filter params to the API', async () => {
    mockedSearchJobs.mockResolvedValueOnce({ items: [], total: 0 });
    renderAt('/v2/search?q=x&type=job&location=ha_noi&job_type=remote&seniority=senior');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalledWith({
        q: 'x',
        top_k: 20,
        location: 'ha_noi',
        job_type: 'remote',
        seniority: 'senior',
      });
    });
  });

  it('switches to CV search when toggle is clicked', async () => {
    mockedSearchJobs.mockResolvedValueOnce({ items: [], total: 0 });
    const cvPayload: CVSearchResponse = {
      items: [
        {
          cv_id: 3001,
          title: 'Sample CV',
          location: 'ha_noi',
          job_type: 'remote',
          seniority: 'senior',
          skills: [],
          score: 0.8,
        },
      ],
      total: 1,
    };
    mockedSearchCvs.mockResolvedValueOnce(cvPayload);

    renderAt('/v2/search?q=python&type=job');

    await waitFor(() => {
      expect(mockedSearchJobs).toHaveBeenCalled();
    });

    await userEvent.click(screen.getByRole('button', { name: /Tìm CV/i }));

    await waitFor(() => {
      expect(mockedSearchCvs).toHaveBeenCalledWith({
        q: 'python',
        top_k: 20,
        location: undefined,
        job_type: undefined,
        seniority: undefined,
      });
    });
    expect(await screen.findByText('Sample CV')).toBeInTheDocument();
  });

  it('shows the empty-state message when total is 0', async () => {
    mockedSearchJobs.mockResolvedValueOnce({ items: [], total: 0 });
    renderAt('/v2/search?q=marketing&type=job');

    expect(
      await screen.findByText(/Không tìm thấy job phù hợp/i)
    ).toBeInTheDocument();
  });

  it('collapses low-score results behind a button when there are high-score ones', async () => {
    // 2 high (0.9, 0.85) + 2 low (0.15, 0.10)
    const items: JobSearchItem[] = [
      ...buildJobs(2, 0.9), // 0.9, 0.85
      {
        job_id: 5000,
        title: 'Low Score Job 1',
        location: 'ha_noi',
        job_type: 'remote',
        seniority: 'mid',
        skills: [],
        score: 0.15,
      },
      {
        job_id: 5001,
        title: 'Low Score Job 2',
        location: 'ha_noi',
        job_type: 'remote',
        seniority: 'mid',
        skills: [],
        score: 0.10,
      },
    ];
    mockedSearchJobs.mockResolvedValueOnce({ items, total: 4 });

    renderAt('/v2/search?q=backend&type=job');

    expect(await screen.findByText('Job 1')).toBeInTheDocument();
    expect(screen.getByText('Job 2')).toBeInTheDocument();
    // Low-score items hidden initially
    expect(screen.queryByText('Low Score Job 1')).not.toBeInTheDocument();

    // Click to expand
    const expand = screen.getByRole('button', { name: /Xem thêm.*kết quả ít liên quan/i });
    await userEvent.click(expand);

    expect(screen.getByText('Low Score Job 1')).toBeInTheDocument();
    expect(screen.getByText('Low Score Job 2')).toBeInTheDocument();
  });

  it('auto-expands low-score results when there are no high-score ones', async () => {
    const items: JobSearchItem[] = [
      {
        job_id: 5000,
        title: 'Only Low',
        location: 'ha_noi',
        job_type: 'remote',
        seniority: 'mid',
        skills: [],
        score: 0.05,
      },
    ];
    mockedSearchJobs.mockResolvedValueOnce({ items, total: 1 });

    renderAt('/v2/search?q=marketing&type=job');

    expect(await screen.findByText('Only Low')).toBeInTheDocument();
    expect(
      screen.getByText(/Không có kết quả phù hợp cao/i)
    ).toBeInTheDocument();
  });
});

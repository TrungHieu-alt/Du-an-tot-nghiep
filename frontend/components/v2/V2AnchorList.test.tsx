import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../src/api/v2', () => ({
  listV2Jobs: vi.fn(),
  listV2Cvs: vi.fn(),
}));

import V2AnchorList from './V2AnchorList';
import { listV2Cvs, listV2Jobs } from '../../src/api/v2';

const mockedListJobs = vi.mocked(listV2Jobs);
const mockedListCvs = vi.mocked(listV2Cvs);

const buildJobs = (offset: number, count: number) =>
  Array.from({ length: count }, (_, i) => ({
    job_id: 4000 + offset + i,
    title: `Job ${offset + i}`,
    location: 'ha_noi' as const,
    job_type: 'fulltime' as const,
    seniority: 'junior' as const,
    skills: ['python', 'sql'],
  }));

const buildCvs = (offset: number, count: number) =>
  Array.from({ length: count }, (_, i) => ({
    cv_id: 3000 + offset + i,
    title: `CV ${offset + i}`,
    location: 'tp_hcm' as const,
    job_type: 'remote' as const,
    seniority: 'mid' as const,
    skills: ['react'],
  }));

describe('V2AnchorList', () => {
  beforeEach(() => {
    mockedListJobs.mockReset();
    mockedListCvs.mockReset();
    // Default: both calls resolve with empty until configured.
    mockedListCvs.mockResolvedValue({ items: [], total: 0 });
  });

  it('renders the job list returned from the API', async () => {
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(0, 3), total: 3 });

    render(
      <V2AnchorList
        anchorType="job"
        selectedId={null}
        onAnchorTypeChange={() => {}}
        onSelect={() => {}}
      />
    );

    expect(await screen.findByText('Job 0')).toBeInTheDocument();
    expect(screen.getByText('Job 1')).toBeInTheDocument();
    expect(screen.getByText('Job 2')).toBeInTheDocument();
    // Pagination summary
    expect(screen.getByText(/3 jobs/i)).toBeInTheDocument();
    expect(mockedListJobs).toHaveBeenCalledWith({ limit: 10, offset: 0 });
  });

  it('invokes onSelect with the integer job_id when an item is clicked', async () => {
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(0, 2), total: 2 });
    const onSelect = vi.fn();

    render(
      <V2AnchorList
        anchorType="job"
        selectedId={null}
        onAnchorTypeChange={() => {}}
        onSelect={onSelect}
      />
    );

    const item = await screen.findByText('Job 1');
    await userEvent.click(item);

    expect(onSelect).toHaveBeenCalledWith(4001, 'job');
  });

  it('paginates next/prev by offset', async () => {
    // First call (offset=0)
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(0, 10), total: 25 });

    render(
      <V2AnchorList
        anchorType="job"
        selectedId={null}
        onAnchorTypeChange={() => {}}
        onSelect={() => {}}
      />
    );

    // Wait first page
    expect(await screen.findByText('Job 0')).toBeInTheDocument();
    expect(screen.getByText(/Trang 1\/3/)).toBeInTheDocument();

    // Next page (offset=10)
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(10, 10), total: 25 });
    await userEvent.click(screen.getByLabelText('Next page'));

    await waitFor(() => {
      expect(mockedListJobs).toHaveBeenLastCalledWith({ limit: 10, offset: 10 });
    });
    expect(await screen.findByText('Job 10')).toBeInTheDocument();
    expect(screen.getByText(/Trang 2\/3/)).toBeInTheDocument();

    // Prev page (offset=0 again)
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(0, 10), total: 25 });
    await userEvent.click(screen.getByLabelText('Previous page'));

    await waitFor(() => {
      expect(mockedListJobs).toHaveBeenLastCalledWith({ limit: 10, offset: 0 });
    });
    expect(screen.getByText(/Trang 1\/3/)).toBeInTheDocument();
  });

  it('switches to the cv tab and triggers a cv fetch', async () => {
    mockedListJobs.mockResolvedValueOnce({ items: buildJobs(0, 1), total: 1 });
    mockedListCvs.mockResolvedValueOnce({ items: buildCvs(0, 2), total: 2 });
    const onAnchorTypeChange = vi.fn();

    const { rerender } = render(
      <V2AnchorList
        anchorType="job"
        selectedId={null}
        onAnchorTypeChange={onAnchorTypeChange}
        onSelect={() => {}}
      />
    );

    // Click By CV — parent handler is informed
    await userEvent.click(screen.getByRole('button', { name: /By CV/i }));
    expect(onAnchorTypeChange).toHaveBeenCalledWith('cv');

    // Simulate parent toggling the prop, which re-renders with cv list
    rerender(
      <V2AnchorList
        anchorType="cv"
        selectedId={null}
        onAnchorTypeChange={onAnchorTypeChange}
        onSelect={() => {}}
      />
    );

    expect(await screen.findByText('CV 0')).toBeInTheDocument();
    expect(screen.getByText('CV 1')).toBeInTheDocument();
    expect(mockedListCvs).toHaveBeenCalled();
  });

  it('filters items locally by the search input', async () => {
    mockedListJobs.mockResolvedValueOnce({
      items: [
        ...buildJobs(0, 1),
        {
          job_id: 9999,
          title: 'Frontend Wizard',
          location: 'ha_noi',
          job_type: 'fulltime',
          seniority: 'senior',
          skills: ['react', 'typescript'],
        },
      ],
      total: 2,
    });

    render(
      <V2AnchorList
        anchorType="job"
        selectedId={null}
        onAnchorTypeChange={() => {}}
        onSelect={() => {}}
      />
    );

    expect(await screen.findByText('Job 0')).toBeInTheDocument();
    expect(screen.getByText('Frontend Wizard')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText(/Tìm theo tiêu đề/i), 'Frontend');

    expect(screen.queryByText('Job 0')).not.toBeInTheDocument();
    expect(screen.getByText('Frontend Wizard')).toBeInTheDocument();
  });
});

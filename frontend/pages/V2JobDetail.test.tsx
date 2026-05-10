import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('../src/api/v2', () => ({
  getV2Job: vi.fn(),
}));

import V2JobDetail from './V2JobDetail';
import { getV2Job } from '../src/api/v2';
import type { JobV2Detail } from '../types';

const mockedGetV2Job = vi.mocked(getV2Job);

const sample: JobV2Detail = {
  job_id: 4001,
  title: 'Senior Backend DevOps Engineer',
  skills: ['python', 'docker', 'kubernetes'],
  requirement: '3+ năm kinh nghiệm backend.',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  education: 'dai_hoc',
  required_certifications: ['aws_saa'],
};

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/v2/jobs/:id" element={<V2JobDetail />} />
      </Routes>
    </MemoryRouter>
  );

describe('V2JobDetail', () => {
  beforeEach(() => {
    mockedGetV2Job.mockReset();
  });

  it('fetches by integer id and renders title + chips + skills', async () => {
    mockedGetV2Job.mockResolvedValueOnce(sample);

    renderAt('/v2/jobs/4001');

    expect(await screen.findByText(sample.title)).toBeInTheDocument();
    expect(mockedGetV2Job).toHaveBeenCalledWith(4001);
    // Vietnamese label appears for the location enum
    expect(screen.getByText('Hà Nội')).toBeInTheDocument();
    expect(screen.getByText('Remote')).toBeInTheDocument();
    expect(screen.getByText('Senior')).toBeInTheDocument();
    expect(screen.getByText('Đại học')).toBeInTheDocument();
    // Skills rendered
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('docker')).toBeInTheDocument();
    // Requirement text
    expect(screen.getByText(/3\+ năm/i)).toBeInTheDocument();
    // Certification
    expect(screen.getByText('aws_saa')).toBeInTheDocument();
  });

  it('Run Matching button links to /v2/matching with anchor=job&id=...', async () => {
    mockedGetV2Job.mockResolvedValueOnce(sample);

    renderAt('/v2/jobs/4001');

    const runLink = await screen.findByRole('link', { name: /Run Matching V2/i });
    expect(runLink).toHaveAttribute('href', '/v2/matching?anchor=job&id=4001');
  });

  it('renders 404 state with link to search when backend returns 404', async () => {
    mockedGetV2Job.mockRejectedValueOnce({ response: { status: 404 } });

    renderAt('/v2/jobs/9999');

    expect(await screen.findByText(/Không tìm thấy job/i)).toBeInTheDocument();
    const back = screen.getByRole('link', { name: /Quay lại tìm kiếm/i });
    expect(back).toHaveAttribute('href', '/v2/search?type=job');
  });

  it('treats non-numeric id as not_found without calling the API', async () => {
    renderAt('/v2/jobs/abc');

    expect(await screen.findByText(/Không tìm thấy job/i)).toBeInTheDocument();
    expect(mockedGetV2Job).not.toHaveBeenCalled();
  });

  it('shows a generic error message on non-404 failures', async () => {
    mockedGetV2Job.mockRejectedValueOnce({ response: { status: 500 } });

    renderAt('/v2/jobs/4001');

    await waitFor(() => {
      // Falls back to default Vietnamese error message.
      expect(screen.getByText(/Đã có lỗi xảy ra/i)).toBeInTheDocument();
    });
  });
});

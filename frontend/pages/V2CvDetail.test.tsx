import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('../src/api/v2', () => ({
  getV2Cv: vi.fn(),
}));

import V2CvDetail from './V2CvDetail';
import { getV2Cv } from '../src/api/v2';
import type { CVV2Detail } from '../types';

const mockedGetV2Cv = vi.mocked(getV2Cv);

const sample: CVV2Detail = {
  cv_id: 3001,
  title: 'Senior Backend DevOps Engineer',
  skills: ['python', 'aws'],
  summary: 'Tóm tắt cá nhân.',
  experience: '5 năm làm backend.',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  education: 'dai_hoc',
  certifications: ['aws_ccp'],
};

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/v2/cvs/:id" element={<V2CvDetail />} />
      </Routes>
    </MemoryRouter>
  );

describe('V2CvDetail', () => {
  beforeEach(() => {
    mockedGetV2Cv.mockReset();
  });

  it('fetches by integer id and renders title, summary, experience', async () => {
    mockedGetV2Cv.mockResolvedValueOnce(sample);

    renderAt('/v2/cvs/3001');

    expect(await screen.findByText(sample.title)).toBeInTheDocument();
    expect(mockedGetV2Cv).toHaveBeenCalledWith(3001);
    expect(screen.getByText('Tóm tắt cá nhân.')).toBeInTheDocument();
    expect(screen.getByText('5 năm làm backend.')).toBeInTheDocument();
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.getByText('aws_ccp')).toBeInTheDocument();
  });

  it('Run Matching button links to /v2/matching with anchor=cv&id=...', async () => {
    mockedGetV2Cv.mockResolvedValueOnce(sample);

    renderAt('/v2/cvs/3001');

    const runLink = await screen.findByRole('link', { name: /Run Matching V2/i });
    expect(runLink).toHaveAttribute('href', '/v2/matching?anchor=cv&id=3001');
  });

  it('renders 404 state when backend returns 404', async () => {
    mockedGetV2Cv.mockRejectedValueOnce({ response: { status: 404 } });

    renderAt('/v2/cvs/9999');

    expect(await screen.findByText(/Không tìm thấy CV/i)).toBeInTheDocument();
    const back = screen.getByRole('link', { name: /Quay lại tìm kiếm/i });
    expect(back).toHaveAttribute('href', '/v2/search?type=cv');
  });

  it('treats non-numeric id as not_found without calling the API', async () => {
    renderAt('/v2/cvs/abc');
    expect(await screen.findByText(/Không tìm thấy CV/i)).toBeInTheDocument();
    expect(mockedGetV2Cv).not.toHaveBeenCalled();
  });
});

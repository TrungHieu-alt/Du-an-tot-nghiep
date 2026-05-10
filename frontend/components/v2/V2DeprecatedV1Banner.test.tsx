import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import V2DeprecatedV1Banner from './V2DeprecatedV1Banner';

const renderBanner = (type: 'job' | 'cv') =>
  render(
    <MemoryRouter>
      <V2DeprecatedV1Banner type={type} />
    </MemoryRouter>
  );

describe('V2DeprecatedV1Banner', () => {
  it('renders the job-side notice and links to /v2/search?type=job', () => {
    renderBanner('job');
    expect(screen.getByText(/trang tìm việc làm/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Thử Search V2/i });
    expect(link).toHaveAttribute('href', '/v2/search?type=job');
  });

  it('renders the cv-side notice and links to /v2/search?type=cv', () => {
    renderBanner('cv');
    expect(screen.getByText(/trang tìm ứng viên/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Thử Search V2/i });
    expect(link).toHaveAttribute('href', '/v2/search?type=cv');
  });

  it('marks the region with an accessible label', () => {
    renderBanner('job');
    expect(
      screen.getByRole('region', { name: /trang search cũ/i })
    ).toBeInTheDocument();
  });
});

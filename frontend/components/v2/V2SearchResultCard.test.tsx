import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import V2SearchResultCard from './V2SearchResultCard';
import type { CVSearchItem, JobSearchItem } from '../../types';

const jobItem: JobSearchItem = {
  job_id: 4001,
  title: 'Senior Backend DevOps Engineer',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  skills: ['python', 'docker', 'kubernetes', 'aws', 'postgres', 'terraform', 'helm'],
  score: 0.834,
};

const cvItem: CVSearchItem = {
  cv_id: 3001,
  title: 'Senior Python Cloud Engineer',
  location: 'ha_noi',
  job_type: 'remote',
  seniority: 'senior',
  skills: ['python', 'docker'],
  score: 0.15,
};

const renderCard = (props: React.ComponentProps<typeof V2SearchResultCard>) =>
  render(
    <MemoryRouter>
      <V2SearchResultCard {...props} />
    </MemoryRouter>
  );

describe('V2SearchResultCard', () => {
  it('renders job card with rounded score and Vietnamese chip labels', () => {
    renderCard({ item: jobItem, type: 'job' });
    expect(screen.getByText(jobItem.title)).toBeInTheDocument();
    expect(screen.getByText('83%')).toBeInTheDocument();
    expect(screen.getByText('Hà Nội')).toBeInTheDocument();
    expect(screen.getByText('Remote')).toBeInTheDocument();
    expect(screen.getByText('Senior')).toBeInTheDocument();
  });

  it('truncates skill list and shows +N more', () => {
    renderCard({ item: jobItem, type: 'job' });
    // 7 skills total, 6 visible, 1 hidden
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(screen.queryByText('helm')).not.toBeInTheDocument();
    expect(screen.getByText('+1 more')).toBeInTheDocument();
  });

  it('links to /v2/jobs/:id for job type', () => {
    renderCard({ item: jobItem, type: 'job' });
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/v2/jobs/4001');
  });

  it('links to /v2/cvs/:id for cv type', () => {
    renderCard({ item: cvItem, type: 'cv' });
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/v2/cvs/3001');
  });

  it('applies low-score variant class when lowScore=true', () => {
    renderCard({ item: cvItem, type: 'cv', lowScore: true });
    const link = screen.getByRole('link');
    expect(link.className).toContain('opacity-70');
  });

  it('clamps score >1 and <0 to [0,100]', () => {
    renderCard({ item: { ...jobItem, score: 1.5 }, type: 'job' });
    expect(screen.getByText('100%')).toBeInTheDocument();

    renderCard({ item: { ...cvItem, score: -0.2 }, type: 'cv' });
    expect(screen.getByText('0%')).toBeInTheDocument();
  });
});

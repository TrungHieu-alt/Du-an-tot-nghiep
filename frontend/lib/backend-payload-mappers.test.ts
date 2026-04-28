import { describe, expect, it } from 'vitest';
import {
  toCandidateResumeUpdatePayload,
  toJobPostUpdatePayload,
} from './backend-payload-mappers';

describe('backend payload mappers', () => {
  it('maps candidate edit payload to CandidateResumeRequest fields', () => {
    const result = toCandidateResumeUpdatePayload(
      {
        headline: 'Senior Frontend Engineer',
        location: { city: 'Ha Noi' },
        skills: [{ name: 'React' }, { name: 'TypeScript' }],
        summary: 'Build UI',
      },
      {
        is_main: true,
        pdf_url: 'https://cdn/cv.pdf',
      }
    );

    expect(result).toEqual({
      title: 'Senior Frontend Engineer',
      location: 'Ha Noi',
      experience: undefined,
      skills: ['React', 'TypeScript'],
      summary: 'Build UI',
      full_text: 'Build UI',
      pdf_url: 'https://cdn/cv.pdf',
      is_main: true,
    });
  });

  it('maps recruiter edit payload to JobPostRequest fields', () => {
    const result = toJobPostUpdatePayload(
      {
        title: 'Frontend Engineer',
        location: 'Da Nang',
        employmentType: ['Remote'],
        experienceLevel: 'Senior',
        skills: ['React', 'Node.js'],
        salaryRange: '1000-1500',
        description: 'Product team role',
        criteria: '- Build FE\n- Review PR',
      },
      {
        role: 'Software Engineer',
      }
    );

    expect(result).toEqual({
      title: 'Frontend Engineer',
      role: 'Software Engineer',
      location: 'Da Nang',
      job_type: 'Remote',
      experience_level: 'Senior',
      skills: ['React', 'Node.js'],
      salary_min: 1000,
      salary_max: 1500,
      full_text: 'Product team role\n\nBuild FE\nReview PR',
      pdf_url: undefined,
    });
  });
});

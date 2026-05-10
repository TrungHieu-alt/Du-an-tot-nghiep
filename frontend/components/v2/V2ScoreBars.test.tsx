import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import V2ScoreBars from './V2ScoreBars';

describe('V2ScoreBars', () => {
  it('renders the four sub-score labels', () => {
    render(
      <V2ScoreBars
        titleScore={0.5}
        skillsScore={0.5}
        reqExpScore={0.5}
        reqSummaryScore={0.5}
      />
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Skills')).toBeInTheDocument();
    expect(screen.getByText('Req ↔ Experience')).toBeInTheDocument();
    expect(screen.getByText('Req ↔ Summary')).toBeInTheDocument();
  });

  it('formats each score as a percentage', () => {
    render(
      <V2ScoreBars
        titleScore={1}
        skillsScore={0.756}
        reqExpScore={0.5}
        reqSummaryScore={0.123}
      />
    );
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('76%')).toBeInTheDocument(); // 0.756 → round → 76
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('12%')).toBeInTheDocument(); // 0.123 → round → 12
  });

  it('renders 0% when all scores are zero (edge case)', () => {
    const { container } = render(
      <V2ScoreBars
        titleScore={0}
        skillsScore={0}
        reqExpScore={0}
        reqSummaryScore={0}
      />
    );
    const zeros = screen.getAllByText('0%');
    expect(zeros).toHaveLength(4);
    // All bar fills must have width 0%
    const fills = container.querySelectorAll('div[style*="width"]');
    expect(fills.length).toBe(4);
    fills.forEach((el) => {
      expect((el as HTMLElement).style.width).toBe('0%');
    });
  });

  it('clamps values above 1 and below 0', () => {
    render(
      <V2ScoreBars
        titleScore={1.5}      // above 1 → 100%
        skillsScore={-0.4}    // below 0 → 0%
        reqExpScore={0.5}
        reqSummaryScore={0.999} // rounds → 100%
      />
    );
    // 1.5 → 100% and 0.999 → 100% so two 100% labels appear
    expect(screen.getAllByText('100%')).toHaveLength(2);
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });
});

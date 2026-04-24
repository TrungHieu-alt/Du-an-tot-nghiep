import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import CvSelectorModal from './CvSelectorModal';
import { ErrorToastProvider } from '../contexts/ErrorToastContext';
import { reportApiError } from '../lib/api-error';

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
  },
}));

describe('CvSelectorModal global toast channel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders API error toast while modal is open', async () => {
    render(
      <ErrorToastProvider>
        <MemoryRouter>
          <CvSelectorModal
            isOpen
            onClose={vi.fn()}
            onSelectCv={vi.fn()}
            onSkip={vi.fn()}
            cvs={[]}
          />
        </MemoryRouter>
      </ErrorToastProvider>
    );

    act(() => {
      reportApiError('Request failed', {
        context: {
          source: 'axios',
          statusCode: 500,
          endpoint: '/cv/user/1',
          method: 'GET',
          payload: { detail: 'Không tải được CV' },
        },
      });
    });

    expect(await screen.findByText('Không tải được CV')).toBeInTheDocument();
  });
});

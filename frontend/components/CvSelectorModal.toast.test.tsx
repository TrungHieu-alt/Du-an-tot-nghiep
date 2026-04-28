import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CvSelectorModal from './CvSelectorModal';
import { ErrorToastProvider } from '../contexts/ErrorToastContext';
import { reportApiError } from '../lib/api-error';
import api from '../lib/api';

vi.mock('../lib/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    delete: vi.fn().mockResolvedValue({ status: 200 }),
  },
}));

describe('CvSelectorModal global toast channel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('user', JSON.stringify({ id: '1' }));
    sessionStorage.clear();
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

  it('removes deleted CV immediately without refetching list on confirm flow', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          _id: 'cv-1',
          title: 'Frontend CV',
          headline: 'Frontend Engineer',
          skills: ['React'],
          user_id: '1',
        },
      ],
    } as any);
    vi.mocked(api.delete).mockResolvedValue({ status: 200 } as any);
    const user = userEvent.setup();

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

    expect(await screen.findByText('Frontend CV')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /mở menu cho frontend cv/i }));
    await user.click(screen.getByRole('button', { name: /xóa frontend cv/i }));
    await user.click(screen.getByRole('button', { name: /^xóa$/i }));

    await waitFor(() => {
      expect(screen.queryByText('Frontend CV')).not.toBeInTheDocument();
    });

    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.delete).toHaveBeenCalledWith('/cv/cv-1');
  });
});

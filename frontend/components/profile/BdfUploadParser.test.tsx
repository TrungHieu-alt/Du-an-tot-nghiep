import React from 'react';
import { fireEvent, render, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import BdfUploadParser from './BdfUploadParser';
import api from '../../lib/api';

vi.mock('../../lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '157' },
  }),
}));

vi.mock('../../lib/auth-session', () => ({
  getCurrentUserId: () => '157',
}));

describe('BdfUploadParser endpoint routing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls CV upload endpoint in cv mode', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { cv_id: 111 } } as never);
    const onParseComplete = vi.fn();
    const { container } = render(<BdfUploadParser mode="cv" onParseComplete={onParseComplete} />);

    const input = container.querySelector('#file-upload') as HTMLInputElement;
    const file = new File(['cv-content'], 'cv.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(api.post).toHaveBeenCalled();
    });
    expect(vi.mocked(api.post).mock.calls[0]?.[0]).toBe('/cv/upload/157');
  });

  it('calls JD upload endpoint in jd mode', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { job_id: 222 } } as never);
    const onParseComplete = vi.fn();
    const { container } = render(<BdfUploadParser mode="jd" onParseComplete={onParseComplete} />);

    const input = container.querySelector('#file-upload') as HTMLInputElement;
    const file = new File(['jd-content'], 'jd.pdf', { type: 'application/pdf' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(api.post).toHaveBeenCalled();
    });
    expect(vi.mocked(api.post).mock.calls[0]?.[0]).toBe('/jobs/upload/157');
  });
});


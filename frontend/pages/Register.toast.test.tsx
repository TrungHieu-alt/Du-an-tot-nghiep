import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Register from './Register';
import { ErrorToastProvider } from '../contexts/ErrorToastContext';

describe('Register page API error toast', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('shows global toast with backend detail on 422 response', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Email đã tồn tại' }), {
        status: 422,
        headers: { 'content-type': 'application/json' },
      })
    ) as unknown as typeof fetch;

    render(
      <ErrorToastProvider>
        <MemoryRouter>
          <Register />
        </MemoryRouter>
      </ErrorToastProvider>
    );

    await userEvent.type(screen.getByLabelText(/Email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/Mật khẩu/i), 'secret123');
    await userEvent.click(screen.getByRole('button', { name: 'Đăng ký tài khoản' }));

    const errorMessages = await screen.findAllByText('Email đã tồn tại');
    expect(errorMessages.length).toBeGreaterThanOrEqual(2);
  });
});

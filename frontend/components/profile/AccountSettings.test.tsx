import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AccountSettings from './AccountSettings';
import api from '../../lib/api';

const logoutMock = vi.fn();
const navigateMock = vi.fn();

vi.mock('../../lib/api', () => ({
  default: {
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ logout: logoutMock, user: { id: '12' } }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('AccountSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  it('shows validation error and skips API call when confirm password mismatches', async () => {
    render(
      <MemoryRouter>
        <AccountSettings />
      </MemoryRouter>
    );

    const oldPassword = document.querySelector('input[name="oldPassword"]') as HTMLInputElement;
    const newPassword = document.querySelector('input[name="newPassword"]') as HTMLInputElement;
    const confirmPassword = document.querySelector('input[name="confirmPassword"]') as HTMLInputElement;
    await userEvent.type(oldPassword, 'old-pass');
    await userEvent.type(newPassword, 'new-pass-123');
    await userEvent.type(confirmPassword, 'different-pass');

    await userEvent.click(screen.getByRole('button', { name: 'Cập nhật mật khẩu' }));

    expect(await screen.findByText('Mật khẩu xác nhận không khớp.')).toBeInTheDocument();
    expect(vi.mocked(api.patch)).not.toHaveBeenCalled();
  });

  it('shows unsupported message for change-password flow', async () => {

    render(
      <MemoryRouter>
        <AccountSettings />
      </MemoryRouter>
    );

    const oldPassword = document.querySelector('input[name="oldPassword"]') as HTMLInputElement;
    const newPassword = document.querySelector('input[name="newPassword"]') as HTMLInputElement;
    const confirmPassword = document.querySelector('input[name="confirmPassword"]') as HTMLInputElement;
    await userEvent.type(oldPassword, 'old-pass');
    await userEvent.type(newPassword, 'new-pass-123');
    await userEvent.type(confirmPassword, 'new-pass-123');

    await userEvent.click(screen.getByRole('button', { name: 'Cập nhật mật khẩu' }));

    expect(api.patch).not.toHaveBeenCalled();
    expect(await screen.findByText('Backend hiện chưa hỗ trợ đổi mật khẩu qua API.')).toBeInTheDocument();
  });

  it('deletes account after confirmation, then logs out and redirects', async () => {
    vi.mocked(api.delete).mockResolvedValue({ status: 200 } as any);

    render(
      <MemoryRouter>
        <AccountSettings />
      </MemoryRouter>
    );

    await userEvent.click(screen.getByRole('button', { name: 'Xóa tài khoản' }));
    await userEvent.click(screen.getByRole('button', { name: 'Xóa vĩnh viễn' }));

    await waitFor(() => {
      expect(api.delete).toHaveBeenCalledWith('/users/12');
    });

    expect(logoutMock).toHaveBeenCalledTimes(1);
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });
});

import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Register from './Register';
import { authApi } from '../src/api/auth';

const navigateMock = vi.fn();

vi.mock('../src/api/auth', () => ({
  authApi: {
    register: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('Register page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  it('submits registration, persists user data, and navigates to login', async () => {
    const registerMock = vi.mocked(authApi.register);
    const user = { user_id: 7, email: 'new@example.com', role: 'candidate' };
    registerMock.mockResolvedValue(user as any);

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );

    await userEvent.type(screen.getByLabelText(/Email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/Mật khẩu/i), 'secret123');
    await userEvent.click(screen.getByRole('button', { name: 'Đăng ký tài khoản' }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        name: '',
        email: 'new@example.com',
        password: 'secret123',
        role: 'candidate',
      });
    });

    expect(localStorage.getItem('accessToken')).toBeNull();
    expect(localStorage.getItem('user')).toBe(
      JSON.stringify({
        id: '7',
        email: 'new@example.com',
        role: 'candidate',
        name: 'new@example.com',
      })
    );
    expect(window.alert).toHaveBeenCalledWith('Đăng ký thành công!');
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });

  it('shows backend error message when registration fails', async () => {
    const registerMock = vi.mocked(authApi.register);
    registerMock.mockRejectedValue(new Error('Email đã tồn tại'));

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>
    );

    await userEvent.type(screen.getByLabelText(/Email/i), 'new@example.com');
    await userEvent.type(screen.getByLabelText(/Mật khẩu/i), 'secret123');
    await userEvent.selectOptions(screen.getByLabelText(/Vai trò/i), 'recruiter');
    await userEvent.click(screen.getByRole('button', { name: 'Đăng ký tài khoản' }));

    expect(registerMock).toHaveBeenCalledWith({
      name: '',
      email: 'new@example.com',
      password: 'secret123',
      role: 'recruiter',
    });

    expect(await screen.findByText('Email đã tồn tại')).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });
});

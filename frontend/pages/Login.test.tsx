import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from './Login';
import api from '../lib/api';

const navigateMock = vi.fn();
const loginMock = vi.fn();

vi.mock('../lib/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: loginMock,
  }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

describe('Login page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();
  });

  it('submits login form, stores session data, and navigates home on success', async () => {
    const apiPost = vi.mocked(api.post);
    const user = { id: '1', email: 'dev@example.com', name: 'Dev Candidate' };
    apiPost.mockResolvedValue({
      data: {
        accessToken: 'token-123',
        user,
      },
    });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    await userEvent.type(screen.getByLabelText('Email'), 'dev@example.com');
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'secret123');
    await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    await waitFor(() => {
      expect(apiPost).toHaveBeenCalledWith('/auth/login', {
        email: 'dev@example.com',
        password: 'secret123',
        rememberMe: false,
      });
    });

    expect(sessionStorage.getItem('accessToken')).toBe('token-123');
    expect(sessionStorage.getItem('user')).toBe(JSON.stringify(user));
    expect(loginMock).toHaveBeenCalledWith('token-123', user);
    expect(navigateMock).toHaveBeenCalledWith('/');
  });

  it('shows exact backend message when login fails with response payload', async () => {
    const apiPost = vi.mocked(api.post);
    apiPost.mockRejectedValue({
      response: {
        data: {
          message: 'Invalid credentials',
        },
      },
    });

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    );

    await userEvent.type(screen.getByLabelText('Email'), 'dev@example.com');
    await userEvent.type(screen.getByLabelText('Mật khẩu'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });
});

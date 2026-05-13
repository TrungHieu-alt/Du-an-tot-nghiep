import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../src/services/googleIdentity', () => ({
  requestGoogleCredential: vi.fn(),
}));

import Register from './Register';
import { useAuth } from '../contexts/AuthContext';
import { requestGoogleCredential } from '../src/services/googleIdentity';

const mockedUseAuth = vi.mocked(useAuth);
const mockedRequestGoogleCredential = vi.mocked(requestGoogleCredential);

const PathProbe = () => {
  const location = useLocation();
  return <span data-testid="path">{location.pathname}</span>;
};

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/register']}>
      <Register />
      <PathProbe />
    </MemoryRouter>
  );

describe('Register page', () => {
  const register = vi.fn();
  const googleLogin = vi.fn();

  beforeEach(() => {
    register.mockReset();
    googleLogin.mockReset();
    mockedRequestGoogleCredential.mockReset();
    mockedUseAuth.mockReturnValue({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      googleLogin,
      register,
      logout: vi.fn(),
      refreshMe: vi.fn(),
    });
  });

  it('does not render role selection', () => {
    renderPage();

    expect(screen.queryByText(/vai trò/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/candidate/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/employer/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tiếp tục với google/i })).toBeInTheDocument();
  });

  it('registers without sending a role', async () => {
    register.mockResolvedValueOnce({
      id: 'user-1',
      email: 'user@example.com',
      full_name: 'Nguyen Van A',
      role: 'user',
    });
    const user = userEvent.setup();

    renderPage();
    await user.type(screen.getByLabelText(/họ tên/i), 'Nguyen Van A');
    await user.type(screen.getByLabelText(/email/i), 'user@example.com');
    await user.type(screen.getByLabelText(/mật khẩu/i, { selector: 'input' }), '12345678');
    await user.click(screen.getByRole('button', { name: /đăng ký tài khoản/i }));

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: '12345678',
        full_name: 'Nguyen Van A',
      });
    });
  });

  it('continues with Google and redirects to normal job search', async () => {
    mockedRequestGoogleCredential.mockResolvedValueOnce('google-id-token');
    googleLogin.mockResolvedValueOnce({
      id: 'user-1',
      email: 'google@example.com',
      full_name: 'Google User',
      role: 'user',
    });
    const user = userEvent.setup();

    renderPage();
    await user.click(screen.getByRole('button', { name: /tiếp tục với google/i }));

    await waitFor(() => {
      expect(mockedRequestGoogleCredential).toHaveBeenCalled();
      expect(googleLogin).toHaveBeenCalledWith({ credential: 'google-id-token' });
      expect(screen.getByTestId('path')).toHaveTextContent('/jobs/search');
    });
  });
});

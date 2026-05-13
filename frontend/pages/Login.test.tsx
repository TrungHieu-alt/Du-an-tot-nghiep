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

import Login from './Login';
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
    <MemoryRouter initialEntries={['/login']}>
      <Login />
      <PathProbe />
    </MemoryRouter>
  );

describe('Login page', () => {
  const login = vi.fn();
  const googleLogin = vi.fn();

  beforeEach(() => {
    login.mockReset();
    googleLogin.mockReset();
    mockedRequestGoogleCredential.mockReset();
    mockedUseAuth.mockReturnValue({
      accessToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login,
      googleLogin,
      register: vi.fn(),
      logout: vi.fn(),
      refreshMe: vi.fn(),
    });
  });

  it('shows the Google login button', () => {
    renderPage();

    expect(screen.getByRole('button', { name: /đăng nhập bằng google/i })).toBeInTheDocument();
  });

  it('logs in with Google and redirects to normal job search', async () => {
    mockedRequestGoogleCredential.mockResolvedValueOnce('google-id-token');
    googleLogin.mockResolvedValueOnce({
      id: 'user-1',
      email: 'google@example.com',
      full_name: 'Google User',
      role: 'user',
    });
    const user = userEvent.setup();

    renderPage();
    await user.click(screen.getByRole('button', { name: /đăng nhập bằng google/i }));

    await waitFor(() => {
      expect(mockedRequestGoogleCredential).toHaveBeenCalled();
      expect(googleLogin).toHaveBeenCalledWith({ credential: 'google-id-token' });
      expect(screen.getByTestId('path')).toHaveTextContent('/jobs/search');
    });
  });

  it('keeps password login working', async () => {
    login.mockResolvedValueOnce({
      id: 'user-1',
      email: 'user@example.com',
      full_name: 'Nguyen Van A',
      role: 'user',
    });
    const user = userEvent.setup();

    renderPage();
    await user.type(screen.getByLabelText(/^email$/i), 'user@example.com');
    await user.type(screen.getByLabelText(/mật khẩu/i, { selector: 'input' }), '12345678');
    await user.click(screen.getByRole('button', { name: /^đăng nhập$/i }));

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: '12345678',
      });
      expect(screen.getByTestId('path')).toHaveTextContent('/jobs/search');
    });
  });
});

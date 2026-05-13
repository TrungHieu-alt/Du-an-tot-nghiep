import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import Header from './Header';
import { useAuth } from '../contexts/AuthContext';

const mockedUseAuth = vi.mocked(useAuth);

const authValue = (logout = vi.fn()) => ({
  accessToken: 'token',
  user: {
    id: 'user-1',
    email: 'nguyen@example.com',
    full_name: 'Nguyen Van A',
    role: 'candidate' as const,
  },
  isAuthenticated: true,
  isLoading: false,
  login: vi.fn(),
  googleLogin: vi.fn(),
  register: vi.fn(),
  logout,
  refreshMe: vi.fn(),
});

const PathProbe = () => {
  const location = useLocation();
  return <span data-testid="path">{location.pathname}</span>;
};

const renderHeader = (initialPath = '/') =>
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Header />
      <PathProbe />
    </MemoryRouter>
  );

describe('Header profile dropdown', () => {
  beforeEach(() => {
    mockedUseAuth.mockReset();
  });

  it('shows only the profile button in the authenticated header', () => {
    mockedUseAuth.mockReturnValue(authValue());

    renderHeader();

    expect(screen.getByRole('button', { name: /nguyen van a/i })).toBeInTheDocument();
    expect(screen.queryByText('CV của tôi')).not.toBeInTheDocument();
    expect(screen.queryByText('Job của tôi')).not.toBeInTheDocument();
    expect(screen.queryByText('Đăng xuất')).not.toBeInTheDocument();
  });

  it('opens the profile menu with normal management routes', async () => {
    mockedUseAuth.mockReturnValue(authValue());
    const user = userEvent.setup();

    renderHeader();
    await user.click(screen.getByRole('button', { name: /nguyen van a/i }));

    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /thông tin cá nhân/i })).toHaveAttribute(
      'href',
      '/profile'
    );
    expect(screen.getByRole('menuitem', { name: /quản lý cv/i })).toHaveAttribute(
      'href',
      '/cvs'
    );
    expect(
      screen.getByRole('menuitem', { name: /quản lý yêu cầu tuyển dụng/i })
    ).toHaveAttribute('href', '/employer/requests');
    expect(screen.getByRole('menuitem', { name: /^đăng xuất$/i })).toBeInTheDocument();
  });

  it('closes the profile menu when clicking outside', async () => {
    mockedUseAuth.mockReturnValue(authValue());
    const user = userEvent.setup();

    renderHeader();
    await user.click(screen.getByRole('button', { name: /nguyen van a/i }));
    expect(screen.getByRole('menu')).toBeInTheDocument();

    await user.click(document.body);

    await waitFor(() => {
      expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    });
  });

  it('logs out from the dropdown and redirects to public job search', async () => {
    const logout = vi.fn();
    mockedUseAuth.mockReturnValue(authValue(logout));
    const user = userEvent.setup();

    renderHeader('/profile');
    await user.click(screen.getByRole('button', { name: /nguyen van a/i }));
    await user.click(screen.getByRole('menuitem', { name: /^đăng xuất$/i }));

    expect(logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('path')).toHaveTextContent('/jobs/search');
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});

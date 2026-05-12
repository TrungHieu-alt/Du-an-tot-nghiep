import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';

import { AppRoutes } from './App';
import { AuthProvider } from './contexts/AuthContext';

const renderRoutes = (route: string) =>
  render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </MemoryRouter>
  );

describe('AppRoutes', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('renders the JobConnect homepage at root', async () => {
    renderRoutes('/');

    expect(
      await screen.findByRole('heading', {
        name: /kết nối ứng viên và nhà tuyển dụng hàng đầu/i,
      })
    ).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /đăng nhập/i })[0]).toHaveAttribute(
      'href',
      '/login'
    );
    expect(screen.getByRole('link', { name: /^trang chủ$/i })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: /^tìm việc$/i })).toHaveAttribute(
      'href',
      '/v2/search'
    );
    expect(screen.getAllByRole('link', { name: /^matching v2$/i })[0]).toHaveAttribute(
      'href',
      '/v2/matching'
    );
    expect(screen.getAllByRole('link', { name: /^tìm việc ngay$/i })[0]).toHaveAttribute(
      'href',
      '/v2/search'
    );
  });

  it('renders the login page', async () => {
    renderRoutes('/login');

    expect(await screen.findByRole('heading', { name: /^đăng nhập$/i })).toBeInTheDocument();
  });

  it('renders the register page', async () => {
    renderRoutes('/register');

    expect(await screen.findByRole('heading', { name: /đăng ký tài khoản/i })).toBeInTheDocument();
  });

  it.each(['/unknown-route', '/v2/unknown-route'])(
    'redirects unknown route %s to v2 search',
    async (route) => {
      renderRoutes(route);

      expect(await screen.findByRole('heading', { name: /nhập từ khóa để bắt đầu/i })).toBeInTheDocument();
      expect(screen.queryByText(route)).not.toBeInTheDocument();
    }
  );

  it.each([
    ['/v2/search', /nhập từ khóa để bắt đầu/i],
    ['/v2/matching', /v2 matching/i],
  ])('renders existing V2 route %s', async (route, heading) => {
    renderRoutes(route);

    expect(await screen.findByRole('heading', { name: heading })).toBeInTheDocument();
  });
});

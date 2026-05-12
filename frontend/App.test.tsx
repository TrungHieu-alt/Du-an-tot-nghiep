import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { AppRoutes } from './App';

describe('AppRoutes', () => {
  it('redirects root to the v2 search route', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>
    );

    expect(await screen.findByRole('heading', { name: /nhập từ khóa để bắt đầu/i })).toBeInTheDocument();
  });

  it.each(['/unknown-route', '/v2/unknown-route'])(
    'redirects unknown route %s to v2 search',
    async (route) => {
      render(
        <MemoryRouter initialEntries={[route]}>
          <AppRoutes />
        </MemoryRouter>
      );

      expect(await screen.findByRole('heading', { name: /nhập từ khóa để bắt đầu/i })).toBeInTheDocument();
      expect(screen.queryByText(route)).not.toBeInTheDocument();
    }
  );
});

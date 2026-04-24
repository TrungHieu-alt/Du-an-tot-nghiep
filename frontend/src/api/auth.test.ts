import { describe, expect, it, vi } from 'vitest';
import { authApi } from './auth';
import { http } from './http';
import { apiRoutes } from '../../lib/api-routes';

vi.mock('./http', () => ({
  http: vi.fn(),
}));

describe('authApi', () => {
  it('register calls canonical users route with POST payload', async () => {
    const httpMock = vi.mocked(http);
    httpMock.mockResolvedValue({
      user_id: 1,
      email: 'dev@example.com',
      role: 'candidate',
    });

    const dto = { email: 'dev@example.com', password: 'secret123', role: 'candidate' as const };
    await authApi.register(dto);

    expect(httpMock).toHaveBeenCalledWith(apiRoutes.users.register(), {
      method: 'POST',
      body: dto,
    });
  });
});

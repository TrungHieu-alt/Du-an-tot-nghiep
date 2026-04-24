import { describe, expect, it, vi } from 'vitest';
import { authApi } from './auth';
import { http } from './http';

vi.mock('./http', () => ({
  http: vi.fn(),
}));

describe('authApi', () => {
  it('register calls legacy auth route with POST payload', async () => {
    const httpMock = vi.mocked(http);
    httpMock.mockResolvedValue({
      accessToken: 'token',
      user: { id: '1', email: 'dev@example.com', name: 'Dev' },
    });

    const dto = { email: 'dev@example.com', password: 'secret123', name: 'Dev' };
    await authApi.register(dto);

    expect(httpMock).toHaveBeenCalledWith('/auth/register', {
      method: 'POST',
      body: dto,
    });
  });
});

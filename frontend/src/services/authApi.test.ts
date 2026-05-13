import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from '../../lib/api';
import { getMe, googleLogin, login, register, type AuthUser, type LoginResponse } from './authApi';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('authApi', () => {
  beforeEach(() => {
    mockedApi.get.mockReset();
    mockedApi.post.mockReset();
  });

  it('registers a user through the auth endpoint', async () => {
    const user: AuthUser = {
      id: '11111111-1111-1111-1111-111111111111',
      email: 'user@example.com',
      full_name: 'Nguyen Van A',
      role: 'user',
    };
    mockedApi.post.mockResolvedValueOnce({ data: user });

    const result = await register({
      email: 'user@example.com',
      password: '12345678',
      full_name: 'Nguyen Van A',
    });

    expect(mockedApi.post).toHaveBeenCalledWith('/auth/register', {
      email: 'user@example.com',
      password: '12345678',
      full_name: 'Nguyen Van A',
    });
    expect(result).toEqual(user);
  });

  it('logs in and returns the token payload', async () => {
    const response: LoginResponse = {
      access_token: 'token',
      token_type: 'bearer',
      user: {
        id: '11111111-1111-1111-1111-111111111111',
        email: 'user@example.com',
        full_name: null,
        role: 'user',
      },
    };
    mockedApi.post.mockResolvedValueOnce({ data: response });

    const result = await login({ email: 'user@example.com', password: '12345678' });

    expect(mockedApi.post).toHaveBeenCalledWith('/auth/login', {
      email: 'user@example.com',
      password: '12345678',
    });
    expect(result).toEqual(response);
  });

  it('logs in with Google through the auth endpoint', async () => {
    const response: LoginResponse = {
      access_token: 'google-token',
      token_type: 'bearer',
      user: {
        id: '11111111-1111-1111-1111-111111111111',
        email: 'google@example.com',
        full_name: 'Google User',
        role: 'user',
      },
    };
    mockedApi.post.mockResolvedValueOnce({ data: response });

    const result = await googleLogin({ credential: 'google-id-token' });

    expect(mockedApi.post).toHaveBeenCalledWith('/auth/google', {
      credential: 'google-id-token',
    });
    expect(result).toEqual(response);
  });

  it('loads the current user with a bearer token', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        id: '11111111-1111-1111-1111-111111111111',
        email: 'user@example.com',
        full_name: null,
        role: 'user',
      },
    });

    await getMe('token');

    expect(mockedApi.get).toHaveBeenCalledWith('/auth/me', {
      headers: {
        Authorization: 'Bearer token',
      },
    });
  });
});

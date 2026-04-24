import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearAuthSession,
  decodeJwtPayload,
  getCurrentUserId,
  getStoredAccessToken,
  getUserIdFromToken,
  persistAuthSession,
} from './auth-session';

describe('auth-session helpers', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it('decodes JWT payload and reads sub as user id', () => {
    const token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signature';
    expect(decodeJwtPayload(token)).toMatchObject({ sub: '123' });
    expect(getUserIdFromToken(token)).toBe('123');
  });

  it('persists session and derives user id from stored user first', () => {
    persistAuthSession('token-1', { id: '44', email: 'u@example.com', name: 'User' }, false);
    expect(getStoredAccessToken()).toBe('token-1');
    expect(getCurrentUserId()).toBe('44');
  });

  it('falls back to token sub when user payload missing', () => {
    sessionStorage.setItem('accessToken', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI4OCJ9.signature');
    expect(getCurrentUserId()).toBe('88');
  });

  it('clears both session and local storage', () => {
    persistAuthSession('token-1', { id: '44', email: 'u@example.com', name: 'User' }, true);
    clearAuthSession();
    expect(sessionStorage.getItem('accessToken')).toBeNull();
    expect(localStorage.getItem('accessToken')).toBeNull();
  });
});

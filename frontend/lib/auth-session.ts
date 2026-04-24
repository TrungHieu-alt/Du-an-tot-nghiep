import { User } from '../types';

interface JwtPayload {
  sub?: string | number;
  [key: string]: unknown;
}

const TOKEN_KEY = 'accessToken';
const USER_KEY = 'user';

const decodeBase64Url = (value: string): string => {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
  return atob(padded);
};

export const decodeJwtPayload = (token: string): JwtPayload | null => {
  const parts = token.split('.');
  if (parts.length < 2) return null;

  try {
    return JSON.parse(decodeBase64Url(parts[1])) as JwtPayload;
  } catch {
    return null;
  }
};

export const getUserIdFromToken = (token: string): string | null => {
  const payload = decodeJwtPayload(token);
  if (payload?.sub === undefined || payload.sub === null) return null;
  return String(payload.sub);
};

export const getStoredAccessToken = (): string | null =>
  sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);

export const getStoredUser = (): User | null => {
  const raw = sessionStorage.getItem(USER_KEY) || localStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
};

export const getCurrentUserId = (): string | null => {
  const user = getStoredUser();
  if (user?.id) return String(user.id);

  const token = getStoredAccessToken();
  if (!token) return null;
  return getUserIdFromToken(token);
};

export const persistAuthSession = (
  accessToken: string,
  user: User,
  rememberMe: boolean
): void => {
  sessionStorage.setItem(TOKEN_KEY, accessToken);
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));

  if (rememberMe) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
};

export const clearAuthSession = (): void => {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

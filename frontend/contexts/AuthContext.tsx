import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  getMe,
  googleLogin as googleLoginRequest,
  login as loginRequest,
  register as registerRequest,
  type AuthUser,
  type GoogleLoginPayload,
  type LoginPayload,
  type RegisterPayload,
} from '../src/services/authApi';

const ACCESS_TOKEN_KEY = 'jobconnect_access_token';
const USER_KEY = 'jobconnect_user';

interface AuthContextValue {
  accessToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<AuthUser>;
  googleLogin: (payload: GoogleLoginPayload) => Promise<AuthUser>;
  register: (payload: RegisterPayload) => Promise<AuthUser>;
  logout: () => void;
  refreshMe: () => Promise<AuthUser | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const readStoredUser = (): AuthUser | null => {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
};

const clearStoredAuth = () => {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
};

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    window.localStorage.getItem(ACCESS_TOKEN_KEY)
  );
  const [user, setUser] = useState<AuthUser | null>(() => readStoredUser());
  const [isLoading, setIsLoading] = useState<boolean>(() =>
    Boolean(window.localStorage.getItem(ACCESS_TOKEN_KEY))
  );

  const logout = useCallback(() => {
    clearStoredAuth();
    setAccessToken(null);
    setUser(null);
    setIsLoading(false);
  }, []);

  const refreshMe = useCallback(async (): Promise<AuthUser | null> => {
    const token = window.localStorage.getItem(ACCESS_TOKEN_KEY);
    if (!token) {
      logout();
      return null;
    }

    setIsLoading(true);
    try {
      const currentUser = await getMe(token);
      window.localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
      setAccessToken(token);
      setUser(currentUser);
      return currentUser;
    } catch {
      logout();
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (!accessToken) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    getMe(accessToken)
      .then((currentUser) => {
        if (cancelled) return;
        window.localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
        setUser(currentUser);
      })
      .catch(() => {
        if (cancelled) return;
        clearStoredAuth();
        setAccessToken(null);
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const login = useCallback(async (payload: LoginPayload): Promise<AuthUser> => {
    const response = await loginRequest(payload);
    window.localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    setAccessToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const googleLogin = useCallback(async (payload: GoogleLoginPayload): Promise<AuthUser> => {
    const response = await googleLoginRequest(payload);
    window.localStorage.setItem(ACCESS_TOKEN_KEY, response.access_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    setAccessToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (payload: RegisterPayload): Promise<AuthUser> => {
    return registerRequest(payload);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      user,
      isAuthenticated: Boolean(accessToken && user),
      isLoading,
      login,
      googleLogin,
      register,
      logout,
      refreshMe,
    }),
    [accessToken, user, isLoading, login, googleLogin, register, logout, refreshMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

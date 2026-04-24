
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../types';
import { clearAuthSession, getStoredAccessToken, getStoredUser, persistAuthSession } from '../lib/auth-session';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (accessToken: string, userData: User, rememberMe?: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = getStoredAccessToken();
    const storedUser = getStoredUser();

    if (token && storedUser) {
      setIsAuthenticated(true);
      setUser(storedUser);
    } else if (token || storedUser) {
      clearAuthSession();
    }
  }, []);

  const login = (accessToken: string, userData: User, rememberMe = false) => {
    persistAuthSession(accessToken, userData, rememberMe);
    setIsAuthenticated(true);
    setUser(userData);
  };

  const logout = () => {
    clearAuthSession();
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

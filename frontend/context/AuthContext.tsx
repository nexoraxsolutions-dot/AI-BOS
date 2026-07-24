"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as apiLogin, register as apiRegister, refreshToken as apiRefreshToken } from '../lib/api';

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string, username?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  refreshAccessToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  loading: false,
  refreshAccessToken: async () => false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('ai_bos_token');
    if (stored) {
      setToken(stored);
    }
  }, []);

  const refreshAccessToken = async (): Promise<boolean> => {
    const refreshToken = localStorage.getItem('ai_bos_refresh_token');
    if (!refreshToken) {
      return false;
    }

    try {
      const response = await apiRefreshToken(refreshToken);
      localStorage.setItem('ai_bos_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('ai_bos_refresh_token', response.refresh_token);
      }
      setToken(response.access_token);
      return true;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      logout();
      return false;
    }
  };

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await apiLogin(email, password);
      localStorage.setItem('ai_bos_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('ai_bos_refresh_token', response.refresh_token);
      }
      setToken(response.access_token);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string, username?: string) => {
    setLoading(true);
    try {
      const response = await apiRegister(email, password, fullName, username);
      localStorage.setItem('ai_bos_token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('ai_bos_refresh_token', response.refresh_token);
      }
      setToken(response.access_token);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('ai_bos_token');
    localStorage.removeItem('ai_bos_refresh_token');
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        login,
        register,
        logout,
        loading,
        refreshAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
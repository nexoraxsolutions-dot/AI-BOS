"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as apiLogin, register as apiRegister, refreshToken as apiRefreshToken, getMyProfile } from '../lib/api';

interface UserInfo {
  id: number;
  email: string;
  full_name?: string | null;
  username?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  company_id?: number | null;
}

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  user: UserInfo | null;
  login: (email: string, password: string) => Promise<UserInfo | undefined>;
  register: (email: string, password: string, fullName?: string, username?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  refreshAccessToken: () => Promise<boolean>;
  refreshUser: () => Promise<UserInfo | null>;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  isAuthenticated: false,
  user: null,
  login: async () => undefined,
  register: async () => {},
  logout: () => {},
  loading: false,
  refreshAccessToken: async () => false,
  refreshUser: async () => null,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('ai_bos_token');
    const storedUser = localStorage.getItem('ai_bos_user');
    if (stored) {
      setToken(stored);
    }
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem('ai_bos_user');
      }
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
      if (response.user) {
        const userInfo = response.user as unknown as UserInfo;
        localStorage.setItem('ai_bos_user', JSON.stringify(response.user));
        setUser(userInfo);
      }
      setToken(response.access_token);
      return response.user as unknown as UserInfo | undefined;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string, username?: string) => {
    setLoading(true);
    try {
      // Registration sends the verification email but the account's email is not
      // verified yet, so we deliberately do NOT persist the returned tokens or log
      // the user in. They must verify their email and then sign in.
      await apiRegister(email, password, fullName, username);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('ai_bos_token');
    localStorage.removeItem('ai_bos_refresh_token');
    localStorage.removeItem('ai_bos_user');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async (): Promise<UserInfo | null> => {
    try {
      const profile = await getMyProfile();
      const userInfo = profile as unknown as UserInfo;
      localStorage.setItem('ai_bos_user', JSON.stringify(profile));
      setUser(userInfo);
      return userInfo;
    } catch (error) {
      console.error('Failed to refresh user:', error);
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        user,
        login,
        register,
        logout,
        loading,
        refreshAccessToken,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { apiClient } from '@/lib/api-client';
import { AuthUser } from '@/lib/types';

export type { AuthUser };

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  signup: (email: string, password: string) => Promise<void>;
  signin: (email: string, password: string) => Promise<void>;
  signout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .me()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signup = useCallback(async (email: string, password: string) => {
    const result = await apiClient.signup(email, password);
    setUser(result.user);
  }, []);

  const signin = useCallback(async (email: string, password: string) => {
    const result = await apiClient.signin(email, password);
    setUser(result.user);
  }, []);

  const signout = useCallback(async () => {
    await apiClient.signout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, signup, signin, signout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginAsDemoRole: (role: 'admin' | 'faculty' | 'student') => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('campussync_token'));
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      if (token) {
        const u = await api.getMe();
        setUser(u);
      } else {
        setUser(null);
      }
    } catch {
      localStorage.removeItem('campussync_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await api.login(email, password);
    localStorage.setItem('campussync_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const loginAsDemoRole = async (role: 'admin' | 'faculty' | 'student') => {
    let email = 'admin@ddugu.ac.in';
    let password = 'Admin@123';

    if (role === 'faculty') {
      email = 'prof.sharma@ddugu.ac.in';
      password = 'Faculty@123';
    } else if (role === 'student') {
      email = 'rahul.cse23@ddugu.ac.in';
      password = 'Student@123';
    }

    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('campussync_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, loginAsDemoRole, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};


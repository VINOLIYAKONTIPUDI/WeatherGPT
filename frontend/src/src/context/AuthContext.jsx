import React, { createContext, useState, useEffect, useContext } from 'react';
import { signupUser, verifyOTP, resendOTP, loginUser, getCurrentUser } from '../services/api';

const TOKEN_KEY = 'weathergpt_auth_token';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [loading, setLoading] = useState(true);

  // Validate active token on app mount
  useEffect(() => {
    async function initAuth() {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (storedToken) {
        try {
          const userData = await getCurrentUser(storedToken);
          setUser(userData);
          setToken(storedToken);
        } catch (err) {
          console.warn('Stored auth token invalid or expired:', err);
          localStorage.removeItem(TOKEN_KEY);
          setUser(null);
          setToken('');
        }
      }
      setLoading(false);
    }
    initAuth();
  }, []);

  const signup = async (name, email, password, confirm_password) => {
    return await signupUser(name, email, password, confirm_password);
  };

  const verify = async (email, otp) => {
    const data = await verifyOTP(email, otp);
    if (data.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    }
    return data;
  };

  const resend = async (email) => {
    return await resendOTP(email);
  };

  const login = async (email, password) => {
    const data = await loginUser(email, password);
    if (data.access_token) {
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    }
    return data;
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setToken('');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        signup,
        verify,
        resend,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

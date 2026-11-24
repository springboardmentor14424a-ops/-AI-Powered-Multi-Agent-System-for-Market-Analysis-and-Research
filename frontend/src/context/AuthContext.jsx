import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);
const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initial check: Validate session with backend via secure HTTP-only cookie
  useEffect(() => {
    // Purge any legacy tokens from localStorage to ensure tokens are never stored in client storage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.clear();

    api.get('/auth/me')
      .then((res) => {
        setUser(res.data);
      })
      .catch(() => {
        // No active session or session expired
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // 15-minute inactivity timer tracking user interactions
  useEffect(() => {
    if (!user) return;

    let timeoutId;

    const performInactivityLogout = async () => {
      try {
        await api.post('/auth/logout');
      } catch (e) {
        // Ignore network errors
      }
      setUser(null);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      sessionStorage.clear();

      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = '/login';
      }
    };

    const resetTimer = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(performInactivityLogout, INACTIVITY_TIMEOUT_MS);
    };

    // Events that reset the inactivity timer
    const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];

    let lastInteraction = Date.now();
    const onUserInteraction = () => {
      const now = Date.now();
      if (now - lastInteraction > 1000) {
        lastInteraction = now;
        resetTimer();
      }
    };

    activityEvents.forEach((event) => {
      window.addEventListener(event, onUserInteraction, { passive: true });
    });

    // Start timer on login
    resetTimer();

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      activityEvents.forEach((event) => {
        window.removeEventListener(event, onUserInteraction);
      });
    };
  }, [user]);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { user: loggedInUser } = response.data;
    setUser(loggedInUser);
    return loggedInUser;
  };

  const register = async (fullName, email, password, confirmPassword) => {
    const response = await api.post('/auth/register', {
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword,
    });
    return response.data;
  };

  const continueWithGoogle = async (googleData) => {
    const response = await api.post('/auth/google', googleData);
    const { user: loggedInUser } = response.data;
    setUser(loggedInUser);
    return loggedInUser;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignore network errors on logout
    }
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.clear();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        continueWithGoogle,
        logout,
      }}
    >
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

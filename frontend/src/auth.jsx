import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setCsrfToken, setUnauthorizedHandler } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true until we know if a session exists
  const [expired, setExpired] = useState(false);

  const clear = useCallback(() => {
    setUser(null);
    setCsrfToken(null);
  }, []);

  // Restore the session after a page reload (the cookie is still there).
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clear();
      setExpired(true);
    });
    api("/auth/me")
      .then((d) => {
        setCsrfToken(d.csrf_token);
        setUser(d.user);
      })
      .catch(clear)
      .finally(() => setLoading(false));
  }, [clear]);

  const login = useCallback(async (email, password) => {
    const d = await api("/auth/login", { method: "POST", body: { email, password } });
    setCsrfToken(d.csrf_token);
    setUser(d.user);
    setExpired(false);
  }, []);

  const register = useCallback(
    (payload) => api("/auth/register", { method: "POST", body: payload }),
    []
  );

  const logout = useCallback(async () => {
    try {
      await api("/auth/logout", { method: "POST" });
    } finally {
      clear();
      setExpired(false);
    }
  }, [clear]);

  const value = useMemo(
    () => ({ user, loading, expired, login, register, logout }),
    [user, loading, expired, login, register, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

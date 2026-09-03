import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, apiErrorMessage, clearTokens, getAccessToken, setTokens } from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  async function login(usernameOrEmail, password) {
    const form = new URLSearchParams();
    form.set("username", usernameOrEmail);
    form.set("password", password);
    try {
      const { data } = await api.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      setTokens(data);
      await loadMe();
      return { ok: true };
    } catch (error) {
      return { ok: false, message: apiErrorMessage(error, "Invalid credentials.") };
    }
  }

  async function register(username, email, password) {
    try {
      await api.post("/auth/register", { username, email, password });
      return await login(email, password);
    } catch (error) {
      return { ok: false, message: apiErrorMessage(error, "Could not create your account.") };
    }
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh: loadMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

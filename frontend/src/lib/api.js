import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({ baseURL: BASE_URL });

const TOKEN_KEY = "ripple_access_token";
const REFRESH_KEY = "ripple_refresh_token";

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(TOKEN_KEY, access_token);
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response?.status;

    if (status === 401 && !original._retry && getRefreshToken()) {
      original._retry = true;
      try {
        refreshPromise =
          refreshPromise ||
          axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: getRefreshToken(),
          });
        const { data } = await refreshPromise;
        refreshPromise = null;
        setTokens({ access_token: data.access_token });
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (refreshError) {
        refreshPromise = null;
        clearTokens();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export function apiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
  }
  return fallback;
}

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('../lib/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
  apiErrorMessage: (err, fallback) => err?.response?.data?.detail || fallback,
  getAccessToken: vi.fn(),
  setTokens: vi.fn(),
  clearTokens: vi.fn(),
}));

import { api, getAccessToken, setTokens, clearTokens } from '../lib/api';

function wrapper({ children }) {
  return <AuthProvider>{children}</AuthProvider>;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AuthProvider / useAuth', () => {
  it('finishes loading with no user when there is no stored access token', async () => {
    getAccessToken.mockReturnValue(null);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('loads the current user on mount when a token exists', async () => {
    getAccessToken.mockReturnValue('a-token');
    api.get.mockResolvedValue({ data: { user_id: '1', username: 'alice' } });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toEqual({ user_id: '1', username: 'alice' });
  });

  it('login() stores tokens and populates the user on success', async () => {
    // Mirror the real localStorage relationship between setTokens/getAccessToken,
    // since loadMe() (called internally by login()) re-checks getAccessToken().
    let storedToken = null;
    getAccessToken.mockImplementation(() => storedToken);
    setTokens.mockImplementation(({ access_token }) => {
      storedToken = access_token;
    });
    api.post.mockResolvedValue({ data: { access_token: 'abc', refresh_token: 'def' } });
    api.get.mockResolvedValue({ data: { user_id: '1', username: 'alice' } });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    let outcome;
    await act(async () => {
      outcome = await result.current.login('alice', 'Passw0rd!');
    });

    expect(outcome.ok).toBe(true);
    expect(setTokens).toHaveBeenCalledWith({ access_token: 'abc', refresh_token: 'def' });
    expect(result.current.user).toEqual({ user_id: '1', username: 'alice' });
  });

  it('login() surfaces the server error message on failure', async () => {
    getAccessToken.mockReturnValue(null);
    api.post.mockRejectedValue({ response: { data: { detail: 'Invalid credentials' } } });

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    let outcome;
    await act(async () => {
      outcome = await result.current.login('alice', 'wrong');
    });

    expect(outcome.ok).toBe(false);
    expect(setTokens).not.toHaveBeenCalled();
  });

  it('logout() clears tokens and the user', async () => {
    getAccessToken.mockReturnValue(null);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => {
      result.current.logout();
    });

    expect(clearTokens).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
  });
});

import { create } from 'zustand';
import { LoginPayload, RegisterPayload, User } from '../types/auth';
import { fetchCurrentUser, loginUser, registerUser } from '../services/auth';

const TOKEN_KEY = 'ai_careermatch_token';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  initialize: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null,
  isAuthenticated: false,
  isLoading: true,
  authError: null,

  initialize: async () => {
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
    if (!token) {
      set({ token: null, user: null, isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const user = await fetchCurrentUser(token);
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
        authError: null,
      });
    } catch {
      // If token is invalid or expired, purge localStorage and reset
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(TOKEN_KEY);
      }
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },

  login: async (payload: LoginPayload) => {
    set({ isLoading: true, authError: null });
    try {
      const res = await loginUser(payload);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, res.access_token);
      }
      set({
        token: res.access_token,
        user: res.user,
        isAuthenticated: true,
        isLoading: false,
        authError: null,
      });
    } catch (err: any) {
      set({
        authError: err instanceof Error ? err.message : 'Login failed. Please check your credentials.',
        isLoading: false,
        isAuthenticated: false,
      });
      throw err;
    }
  },

  register: async (payload: RegisterPayload) => {
    set({ isLoading: true, authError: null });
    try {
      const res = await registerUser(payload);
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(TOKEN_KEY, res.access_token);
      }
      set({
        token: res.access_token,
        user: res.user,
        isAuthenticated: true,
        isLoading: false,
        authError: null,
      });
    } catch (err: any) {
      set({
        authError: err instanceof Error ? err.message : 'Registration failed.',
        isLoading: false,
        isAuthenticated: false,
      });
      throw err;
    }
  },

  logout: () => {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
    }
    set({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      authError: null,
    });
  },

  clearError: () => set({ authError: null }),
}));

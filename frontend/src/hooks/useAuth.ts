import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';
import { api } from '@/lib/api';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: true,

      login: async (username: string, password: string) => {
        const { access_token } = await api.login(username, password);
        api.setToken(access_token);
        set({ token: access_token, isAuthenticated: true });
        
        // Fetch user info
        const user = await api.getMe();
        set({ user, isLoading: false });
      },

      logout: () => {
        api.setToken(null);
        set({ token: null, user: null, isAuthenticated: false, isLoading: false });
      },

      checkAuth: async () => {
        const { token } = get();
        if (token) {
          api.setToken(token);
          try {
            const user = await api.getMe();
            set({ user, isAuthenticated: true, isLoading: false });
          } catch {
            get().logout();
          }
        } else {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
);

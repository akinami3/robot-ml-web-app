/**
 * Auth store using Zustand.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthTokens, User, UserRole } from "@/types";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;

  setTokens: (tokens: AuthTokens) => void;
  setUser: (user: User) => void;
  logout: () => void;
  hasRole: (...roles: UserRole[]) => boolean;
  canControlRobot: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setTokens: (tokens: AuthTokens) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isAuthenticated: true,
        }),

      setUser: (user: User) => set({ user }),

      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),

      hasRole: (...roles: UserRole[]) => {
        const user = get().user;
        return user ? roles.includes(user.role) : false;
      },

      canControlRobot: () => {
        const user = get().user;
        return user ? ["admin", "operator"].includes(user.role) : false;
      },
    }),
    {
      name: "robot-ai-auth",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);

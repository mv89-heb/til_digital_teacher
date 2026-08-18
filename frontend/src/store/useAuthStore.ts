import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

interface User {
  id: number;
  email: string;
  role: string;
  xp_total?: number;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateXp: (xpTotal: number) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
      updateXp: (xpTotal) =>
        set((state) => (state.user ? { user: { ...state.user, xp_total: xpTotal } } : state)),
    }),
    {
      name: 'auth-session',
      // JWT is intentionally kept in sessionStorage rather than localStorage.
      // It is still readable by page JavaScript, but it does not survive a
      // browser restart. A future HttpOnly-cookie migration can remove this
      // client-side token entirely without changing the store contract.
      storage: createJSONStorage(() => sessionStorage),
    }
  )
)

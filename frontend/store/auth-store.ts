import { create } from "zustand";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
  org_id: string;
};

type AuthState = {
  user: AuthUser | null;
  setUser: (user: AuthUser | null) => void;
};

/**
 * Lightweight client-side auth mirror; authoritative state remains in HTTP-only cookies.
 */
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

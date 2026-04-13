import { create } from "zustand";
import type { UserProfile } from "@/types";
import { queryClient } from "@/lib/query-client";
import { useFiltersStore } from "@/store/filters.store";

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (token: string, user: UserProfile) => void;
  setUser: (user: UserProfile) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (token, user) => {
    localStorage.setItem("access_token", token);
    set({ token, user, isAuthenticated: true, isLoading: false });
  },

  setUser: (user) => {
    set({ user });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    queryClient.clear();
    useFiltersStore.getState().resetFilters();
    set({ token: null, user: null, isAuthenticated: false, isLoading: false });
  },

  hydrate: () => {
    const token = localStorage.getItem("access_token");
    if (token) {
      set({ token, isAuthenticated: true, isLoading: false });
    } else {
      set({ isLoading: false });
    }
  },
}));

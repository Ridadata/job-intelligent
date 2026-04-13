import { create } from "zustand";

type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const stored = (localStorage.getItem("theme") as Theme) || "system";
  // Apply on load
  if (typeof document !== "undefined") applyTheme(stored);

  return {
    theme: stored,

    setTheme: (theme) => {
      localStorage.setItem("theme", theme);
      applyTheme(theme);
      set({ theme });
    },

    toggleTheme: () => {
      const current = get().theme;
      const next: Theme = current === "light" ? "dark" : current === "dark" ? "system" : "light";
      get().setTheme(next);
    },
  };
});

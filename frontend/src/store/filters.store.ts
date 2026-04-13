import { create } from "zustand";

interface FiltersState {
  query: string;
  location: string;
  contractType: string;
  skills: string[];
  salaryMin: number | undefined;
  salaryMax: number | undefined;
  setFilter: <K extends keyof FiltersState>(key: K, value: FiltersState[K]) => void;
  resetFilters: () => void;
}

const initialState = {
  query: "",
  location: "",
  contractType: "",
  skills: [] as string[],
  salaryMin: undefined as number | undefined,
  salaryMax: undefined as number | undefined,
};

export const useFiltersStore = create<FiltersState>((set) => ({
  ...initialState,
  setFilter: (key, value) => set({ [key]: value }),
  resetFilters: () => set(initialState),
}));

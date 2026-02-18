import { create } from "zustand";

interface ConfigStore {
  currentConfigId: string | null;
  setConfigId: (id: string) => void;
}

export const useConfigStore = create<ConfigStore>((set) => ({
  currentConfigId: null,
  setConfigId: (id) => set({ currentConfigId: id }),
}));

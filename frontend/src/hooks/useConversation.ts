"use client";

import { create } from "zustand";

interface ConversationStore {
  currentConversationId: string | null;
  setConversationId: (id: string | null) => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  currentConversationId: null,
  setConversationId: (id) => set({ currentConversationId: id }),
}));

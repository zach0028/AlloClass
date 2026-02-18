"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConfigStore } from "./useConfig";
import { useConversationStore } from "./useConversation";
import { API_BASE, apiFetch } from "@/lib/api";
import type { ConversationResponse } from "@/types/api";

export type MessageRole = "user" | "assistant";

export interface AgentStep {
  tool: string;
  label: string;
  status: "running" | "done" | "error";
  summary?: string;
}

export interface LearningLevel {
  active: boolean;
  message: string;
  proposed_rule?: Record<string, unknown> | null;
  calibration_warning?: string | null;
}

export interface LearningCard {
  level_1: LearningLevel;
  level_2: LearningLevel;
  level_3: LearningLevel;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  steps: AgentStep[];
  data: Record<string, unknown> | null;
  learningCard?: LearningCard | null;
  timestamp: Date;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const skipLoadRef = useRef(false);
  const queryClient = useQueryClient();

  const configId = useConfigStore((s) => s.currentConfigId);
  const conversationId = useConversationStore((s) => s.currentConversationId);
  const setConversationId = useConversationStore((s) => s.setConversationId);

  useEffect(() => {
    if (skipLoadRef.current) {
      skipLoadRef.current = false;
      return;
    }

    if (!conversationId) {
      setMessages([]);
      return;
    }

    apiFetch<{ id: string; role: string; content: string; created_at: string; metadata_?: Record<string, unknown> | null }[]>(
      `/api/conversations/${conversationId}/messages`
    )
      .then((msgs) => {
        setMessages(
          msgs
            .filter((m) => m.role === "user" || m.role === "assistant")
            .map((m) => ({
              id: m.id,
              role: m.role as MessageRole,
              content: m.content,
              steps: [],
              data: (m.metadata_?.tool_results as Record<string, unknown>[] | undefined)?.[0] as Record<string, unknown> | null ?? null,
              learningCard: (m.metadata_?.learning_card as LearningCard | undefined) ?? null,
              timestamp: new Date(m.created_at),
            }))
        );
      })
      .catch(() => setMessages([]));
  }, [conversationId]);

  const addMessage = useCallback(
    (role: MessageRole, content: string, data: Record<string, unknown> | null = null) => {
      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        role,
        content,
        steps: [],
        data,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, msg]);
      return msg.id;
    },
    []
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!configId || isStreaming) return;

      let activeConversationId = conversationId;
      if (!activeConversationId) {
        const conv = await apiFetch<ConversationResponse>("/api/conversations", {
          method: "POST",
          body: JSON.stringify({ config_id: configId }),
        });
        activeConversationId = conv.id;
        skipLoadRef.current = true;
        setConversationId(conv.id);
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      }

      addMessage("user", text);

      const botId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        { id: botId, role: "assistant", content: "", steps: [], data: null, timestamp: new Date() },
      ]);

      setIsStreaming(true);
      const abort = new AbortController();
      abortRef.current = abort;

      try {
        const res = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            config_id: configId,
            conversation_id: activeConversationId,
          }),
          signal: abort.signal,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          setMessages((prev) =>
            prev.map((m) =>
              m.id === botId ? { ...m, content: err.detail ?? "Erreur serveur" } : m
            )
          );
          return;
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) return;

        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.startsWith("event:")) {
              const eventType = line.replace("event:", "").trim();
              const dataLine = lines[i + 1];
              if (!dataLine?.startsWith("data:")) continue;
              i++;

              const payload = dataLine.replace("data:", "").trim();
              let parsed: Record<string, unknown> = {};
              try {
                parsed = JSON.parse(payload);
              } catch {
                parsed = { message: payload };
              }

              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== botId) return m;

                  if (eventType === "delta") {
                    return { ...m, content: m.content + String(parsed.content ?? "") };
                  }
                  if (eventType === "thinking") {
                    return { ...m, content: "" };
                  }
                  if (eventType === "done") {
                    const allDone = m.steps.map((s) =>
                      s.status === "running" ? { ...s, status: "done" as const } : s
                    );
                    return { ...m, steps: allDone };
                  }
                  if (eventType === "step") {
                    const tool = String(parsed.tool ?? "");
                    const label = String(parsed.message ?? "");
                    const newStep: AgentStep = { tool, label, status: "running" };
                    return { ...m, steps: [...m.steps, newStep] };
                  }
                  if (eventType === "step_result") {
                    const tool = String(parsed.tool ?? "");
                    const summary = String(parsed.summary ?? "");
                    const updatedSteps = [...m.steps];
                    const stepIndex = updatedSteps.findLastIndex((s) => s.tool === tool);
                    if (stepIndex !== -1) {
                      updatedSteps[stepIndex] = {
                        ...updatedSteps[stepIndex],
                        status: summary.startsWith("Echec") ? "error" : "done",
                        summary,
                      };
                    }
                    return { ...m, steps: updatedSteps };
                  }
                  if (eventType === "learning") {
                    return {
                      ...m,
                      learningCard: parsed as unknown as LearningCard,
                    };
                  }
                  if (eventType === "tool_data") {
                    const toolResult = parsed.result as Record<string, unknown> | undefined;
                    return {
                      ...m,
                      data: toolResult ? { ...m.data, ...toolResult } : m.data,
                    };
                  }
                  if (eventType === "error") {
                    return { ...m, content: String(parsed.message ?? "Erreur") };
                  }
                  return m;
                })
              );
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === botId ? { ...m, content: "Connexion perdue" } : m
            )
          );
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      }
    },
    [configId, conversationId, isStreaming, addMessage, setConversationId, queryClient]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const newConversation = useCallback(() => {
    setConversationId(null);
  }, [setConversationId]);

  return {
    messages,
    isStreaming,
    sendMessage,
    stopStreaming,
    configId,
    conversationId,
    newConversation,
  };
}

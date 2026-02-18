"use client";

import { useCallback, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";

export type PipelinePhase = "reformulating" | "classifying" | "evaluating";

export interface PhaseState {
  phase: PipelinePhase;
  status: "start" | "done";
  round: number;
  detail?: string;
  classification_id?: string;
}

export interface TicketTrajectory {
  classification_id: string;
  original_text: string;
  original_confidence: number;
  confidences: number[];
  reformulations: string[];
  used_fallbacks: boolean[];
  frozen: boolean[];
  results_per_axis: {
    axis_name: string;
    category_name: string;
    confidence: number;
  }[][];
  errors: (string | null)[];
}

export interface TicketEvaluation {
  classification_id: string;
  meaning_preserved: boolean;
  confidence_analysis: string;
}

export interface RoundRule {
  round: number;
  rules_added: string[];
  rules_removed: string[];
  rules_modified: { old_rule: string; new_rule: string }[];
  diagnosis: string;
  ticket_evaluations: TicketEvaluation[];
}

export type LoopStatus = "idle" | "running" | "done";

export interface GroundTruthConfig {
  ticketCount: number;
  mode: "rounds" | "threshold";
  maxRounds: number;
  targetConfidence: number;
}

export function useGroundTruthSSE(configId: string | null) {
  const [status, setStatus] = useState<LoopStatus>("idle");
  const [currentRound, setCurrentRound] = useState(0);
  const [tickets, setTickets] = useState<TicketTrajectory[]>([]);
  const [roundRules, setRoundRules] = useState<RoundRule[]>([]);
  const [accumulatedRules, setAccumulatedRules] = useState<string[]>([]);
  const [doneMessage, setDoneMessage] = useState("");
  const [currentPhase, setCurrentPhase] = useState<PhaseState | null>(null);
  const [effectiveMax, setEffectiveMax] = useState(5);

  const abortRef = useRef<AbortController | null>(null);

  const launch = useCallback(
    async (config: GroundTruthConfig) => {
      if (!configId || status === "running") return;

      const maxR = config.mode === "rounds" ? config.maxRounds : 15;
      setEffectiveMax(maxR);
      setStatus("running");
      setCurrentRound(0);
      setTickets([]);
      setRoundRules([]);
      setAccumulatedRules([]);
      setDoneMessage("");
      setCurrentPhase(null);

      const abort = new AbortController();
      abortRef.current = abort;

      try {
        const res = await fetch(`${API_BASE}/api/evaluate/ground-truth`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            config_id: configId,
            ticket_count: config.ticketCount,
            max_rounds: config.mode === "rounds" ? config.maxRounds : null,
            target_confidence: config.targetConfidence / 100,
          }),
          signal: abort.signal,
        });

        if (!res.ok) {
          setDoneMessage("Erreur serveur");
          setStatus("done");
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
            if (!line.startsWith("event:")) continue;

            const eventType = line.replace("event:", "").trim();
            const dataLine = lines[i + 1];
            if (!dataLine?.startsWith("data:")) continue;
            i++;

            const payload = dataLine.replace("data:", "").trim();
            let parsed: Record<string, unknown> = {};
            try {
              parsed = JSON.parse(payload);
            } catch {
              continue;
            }

            if (eventType === "init") {
              const initTickets = (
                parsed.tickets as {
                  classification_id: string;
                  original_text: string;
                  original_confidence: number;
                }[]
              ) ?? [];
              setTickets(
                initTickets.map((t) => ({
                  classification_id: t.classification_id,
                  original_text: t.original_text,
                  original_confidence: t.original_confidence,
                  confidences: [],
                  reformulations: [],
                  used_fallbacks: [],
                  frozen: [],
                  results_per_axis: [],
                  errors: [],
                }))
              );
            }

            if (eventType === "round_start") {
              setCurrentRound(parsed.round as number);
            }

            if (eventType === "phase") {
              setCurrentPhase({
                phase: parsed.phase as PipelinePhase,
                status: parsed.status as "start" | "done",
                round: parsed.round as number,
                detail: parsed.detail as string | undefined,
                classification_id: parsed.classification_id as string | undefined,
              });
            }

            if (eventType === "ticket_result") {
              const cid = parsed.classification_id as string;
              const confidence = parsed.confidence as number;
              const reformText = parsed.reformulated_text as string;
              const fallback = (parsed.used_fallback ?? false) as boolean;
              const isFrozen = (parsed.frozen ?? false) as boolean;
              const axisResults = (parsed.results_per_axis ?? []) as {
                axis_name: string;
                category_name: string;
                confidence: number;
              }[];

              setTickets((prev) =>
                prev.map((t) =>
                  t.classification_id === cid
                    ? {
                        ...t,
                        confidences: [...t.confidences, confidence],
                        reformulations: [...t.reformulations, reformText],
                        used_fallbacks: [...t.used_fallbacks, fallback],
                        frozen: [...t.frozen, isFrozen],
                        results_per_axis: [...t.results_per_axis, axisResults],
                        errors: [...t.errors, null],
                      }
                    : t
                )
              );
            }

            if (eventType === "ticket_error") {
              const cid = parsed.classification_id as string;
              const errorMsg = parsed.error as string;
              setTickets((prev) =>
                prev.map((t) =>
                  t.classification_id === cid
                    ? {
                        ...t,
                        confidences: [...t.confidences, 0],
                        reformulations: [...t.reformulations, ""],
                        used_fallbacks: [...t.used_fallbacks, false],
                        frozen: [...t.frozen, false],
                        results_per_axis: [...t.results_per_axis, []],
                        errors: [...t.errors, errorMsg],
                      }
                    : t
                )
              );
            }

            if (eventType === "round_complete") {
              setCurrentPhase(null);
              setRoundRules((prev) => [
                ...prev,
                {
                  round: parsed.round as number,
                  rules_added: (parsed.rules_added ?? []) as string[],
                  rules_removed: (parsed.rules_removed ?? []) as string[],
                  rules_modified: (parsed.rules_modified ?? []) as {
                    old_rule: string;
                    new_rule: string;
                  }[],
                  diagnosis: (parsed.diagnosis ?? "") as string,
                  ticket_evaluations: (parsed.ticket_evaluations ??
                    []) as TicketEvaluation[],
                },
              ]);
              setAccumulatedRules(
                (parsed.accumulated_rules ?? []) as string[]
              );
            }

            if (eventType === "done") {
              setCurrentPhase(null);
              setDoneMessage((parsed.message ?? "Termine") as string);
              setStatus("done");
            }

            if (eventType === "error") {
              setCurrentPhase(null);
              setDoneMessage((parsed.message ?? "Erreur") as string);
              setStatus("done");
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setDoneMessage("Connexion perdue");
        }
        setStatus("done");
      }
    },
    [configId, status]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("done");
    setDoneMessage("Arrete par l'utilisateur");
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setDoneMessage("");
    setCurrentPhase(null);
  }, []);

  return {
    status,
    currentRound,
    effectiveMax,
    tickets,
    roundRules,
    accumulatedRules,
    doneMessage,
    currentPhase,
    launch,
    stop,
    reset,
  };
}

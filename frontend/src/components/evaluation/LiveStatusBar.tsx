"use client";

import { Loader2, Square } from "lucide-react";
import type { PhaseState } from "@/hooks/useGroundTruthSSE";

interface LiveStatusBarProps {
  currentRound: number;
  maxRounds: number;
  currentPhase: PhaseState | null;
  avgConfidence: number | null;
  aboveThreshold: number;
  ticketCount: number;
  onStop: () => void;
}

function getPhaseLabel(phase: PhaseState | null): string {
  if (!phase) return "En attente...";
  if (phase.status === "done") {
    switch (phase.phase) {
      case "reformulating":
        return "Reformulation terminee";
      case "classifying":
        return "Classification terminee";
      case "evaluating":
        return "Evaluation terminee";
    }
  }
  switch (phase.phase) {
    case "reformulating":
      return "Reformulation des tickets en cours...";
    case "classifying":
      return phase.detail
        ? `Classification du ticket ${phase.detail}...`
        : "Classification en cours...";
    case "evaluating":
      return "Le juge evalue le round...";
    default:
      return "En cours...";
  }
}

export function LiveStatusBar({
  currentRound,
  maxRounds,
  currentPhase,
  avgConfidence,
  aboveThreshold,
  ticketCount,
  onStop,
}: LiveStatusBarProps) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <div>
            <p className="text-sm font-semibold">
              Round {currentRound}/{maxRounds}
            </p>
            <p className="text-xs text-muted-foreground">
              {getPhaseLabel(currentPhase)}
            </p>
          </div>
        </div>
        <button
          onClick={onStop}
          className="inline-flex items-center gap-1.5 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-1.5 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10"
        >
          <Square className="h-3 w-3" />
          Arreter
        </button>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${(currentRound / maxRounds) * 100}%` }}
        />
      </div>

      {avgConfidence !== null && (
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span>
            Confiance moyenne : {(avgConfidence * 100).toFixed(1)}%
          </span>
          <span>
            {aboveThreshold}/{ticketCount} au-dessus du seuil
          </span>
        </div>
      )}
    </div>
  );
}

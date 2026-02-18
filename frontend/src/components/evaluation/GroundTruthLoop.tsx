"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle } from "lucide-react";
import { useConfigStore } from "@/hooks/useConfig";
import { useGroundTruthSSE } from "@/hooks/useGroundTruthSSE";
import { ConfigPanel } from "./ConfigPanel";
import { LiveStatusBar } from "./LiveStatusBar";
import { ConfidenceMatrix } from "./ConfidenceMatrix";
import { JudgePanel } from "./JudgePanel";
import { TicketDetailAccordion } from "./TicketDetailAccordion";

export function GroundTruthLoop() {
  const { currentConfigId } = useConfigStore();
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null);
  const [targetConfidence, setTargetConfidence] = useState(90);

  const {
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
  } = useGroundTruthSSE(currentConfigId);

  const hasData = tickets.length > 0 && tickets[0].confidences.length > 0;
  const avgConfidence =
    hasData
      ? tickets.reduce((sum, t) => sum + (t.confidences.at(-1) ?? 0), 0) /
        tickets.length
      : null;
  const aboveThreshold = hasData
    ? tickets.filter(
        (t) => (t.confidences.at(-1) ?? 0) >= targetConfidence / 100
      ).length
    : 0;

  const handleToggleTicket = (id: string) => {
    setExpandedTicket(expandedTicket === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {status === "idle" && (
        <ConfigPanel
          disabled={!currentConfigId}
          onLaunch={(config) => {
            setTargetConfidence(config.targetConfidence);
            launch(config);
          }}
        />
      )}

      {status === "running" && (
        <LiveStatusBar
          currentRound={currentRound}
          maxRounds={effectiveMax}
          currentPhase={currentPhase}
          avgConfidence={avgConfidence}
          aboveThreshold={aboveThreshold}
          ticketCount={tickets.length}
          onStop={stop}
        />
      )}

      {status === "done" && doneMessage && (
        <div
          className={`flex items-center gap-3 rounded-xl border p-4 shadow-sm ${
            aboveThreshold === tickets.length && tickets.length > 0
              ? "border-chart-3/30 bg-chart-3/5 text-chart-3"
              : "border-chart-4/30 bg-chart-4/5 text-chart-4"
          }`}
        >
          {aboveThreshold === tickets.length && tickets.length > 0 ? (
            <CheckCircle2 className="h-5 w-5 shrink-0" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0" />
          )}
          <p className="text-sm font-medium">{doneMessage}</p>
          <button
            onClick={reset}
            className="ml-auto rounded-md border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-accent"
          >
            Relancer
          </button>
        </div>
      )}

      {(hasData || (status === "running" && tickets.length > 0)) && (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <ConfidenceMatrix
              tickets={tickets}
              maxRounds={effectiveMax}
              targetConfidence={targetConfidence / 100}
              currentPhase={currentPhase}
              onTicketClick={handleToggleTicket}
            />
          </div>
          <div className="lg:col-span-2">
            <JudgePanel
              roundRules={roundRules}
              accumulatedRules={accumulatedRules}
              tickets={tickets}
              status={status}
            />
          </div>
        </div>
      )}

      {hasData && (
        <TicketDetailAccordion
          tickets={tickets}
          targetConfidence={targetConfidence / 100}
          expandedTicket={expandedTicket}
          onToggle={handleToggleTicket}
        />
      )}
    </div>
  );
}

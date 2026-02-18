"use client";

import { AlertTriangle, Lock, TrendingUp } from "lucide-react";
import type { PhaseState, TicketTrajectory } from "@/hooks/useGroundTruthSSE";

interface ConfidenceMatrixProps {
  tickets: TicketTrajectory[];
  maxRounds: number;
  targetConfidence: number;
  currentPhase: PhaseState | null;
  onTicketClick: (id: string) => void;
}

export function ConfidenceMatrix({
  tickets,
  maxRounds,
  targetConfidence,
  currentPhase,
  onTicketClick,
}: ConfidenceMatrixProps) {
  const roundColumns = Array.from({ length: maxRounds }, (_, i) => i + 1);

  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-6 py-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <TrendingUp className="h-4 w-4 text-primary" />
          Trajectoire de confiance
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="w-[200px] px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
                Ticket
              </th>
              <th className="w-[60px] px-2 py-3 text-center text-xs font-semibold text-muted-foreground">
                Orig.
              </th>
              {roundColumns.map((r) => (
                <th
                  key={r}
                  className="w-[80px] px-2 py-3 text-center text-xs font-semibold text-muted-foreground"
                >
                  R{r}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {tickets.map((ticket, idx) => (
              <MatrixRow
                key={ticket.classification_id}
                ticket={ticket}
                index={idx}
                maxRounds={maxRounds}
                targetConfidence={targetConfidence}
                currentPhase={currentPhase}
                onClick={() => onTicketClick(ticket.classification_id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MatrixRow({
  ticket,
  index,
  maxRounds,
  targetConfidence,
  currentPhase,
  onClick,
}: {
  ticket: TicketTrajectory;
  index: number;
  maxRounds: number;
  targetConfidence: number;
  currentPhase: PhaseState | null;
  onClick: () => void;
}) {
  const roundColumns = Array.from({ length: maxRounds }, (_, i) => i + 1);

  return (
    <tr
      onClick={onClick}
      className="cursor-pointer transition-colors hover:bg-accent/50"
    >
      <td className="px-4 py-3">
        <p className="max-w-[180px] truncate text-sm font-medium">
          <span className="mr-1.5 text-xs text-muted-foreground">
            #{index + 1}
          </span>
          {ticket.original_text}
        </p>
      </td>

      <td className="px-2 py-3 text-center">
        <span className="text-xs text-muted-foreground">
          {(ticket.original_confidence * 100).toFixed(0)}%
        </span>
      </td>

      {roundColumns.map((roundNum) => {
        const roundIdx = roundNum - 1;
        const hasData = roundIdx < ticket.confidences.length;
        const confidence = hasData ? ticket.confidences[roundIdx] : null;
        const hasError = hasData && ticket.errors[roundIdx] != null;
        const isFrozen = hasData && ticket.frozen[roundIdx];

        const isProcessing =
          currentPhase?.phase === "classifying" &&
          currentPhase?.status === "start" &&
          currentPhase?.classification_id === ticket.classification_id &&
          currentPhase?.round === roundNum;

        const isRoundActive =
          currentPhase?.round === roundNum &&
          currentPhase?.status === "start" &&
          !hasData &&
          (currentPhase?.phase === "reformulating" ||
            currentPhase?.phase === "evaluating");

        return (
          <td key={roundNum} className="px-2 py-3 text-center">
            {isProcessing ? (
              <span className="inline-flex h-8 w-14 items-center justify-center rounded-md border border-primary/30 bg-primary/5">
                <span className="h-2 w-2 animate-ping rounded-full bg-primary" />
              </span>
            ) : hasError ? (
              <span className="inline-flex h-8 w-14 items-center justify-center rounded-md border border-destructive/30 bg-destructive/5 text-destructive">
                <AlertTriangle className="h-3.5 w-3.5" />
              </span>
            ) : hasData && confidence !== null ? (
              <ConfidenceBadge
                confidence={confidence}
                targetConfidence={targetConfidence}
                frozen={isFrozen}
              />
            ) : isRoundActive ? (
              <span className="inline-flex h-8 w-14 animate-pulse items-center justify-center rounded-md border border-dashed border-muted-foreground/30">
                <span className="text-[10px] text-muted-foreground">...</span>
              </span>
            ) : (
              <span className="inline-flex h-8 w-14 items-center justify-center rounded-md border border-dashed border-border" />
            )}
          </td>
        );
      })}
    </tr>
  );
}

function ConfidenceBadge({
  confidence,
  targetConfidence,
  frozen,
}: {
  confidence: number;
  targetConfidence: number;
  frozen: boolean;
}) {
  if (frozen) {
    return (
      <span className="inline-flex h-8 w-14 items-center justify-center gap-0.5 rounded-md border border-chart-3/30 bg-chart-3/10 text-xs font-semibold text-chart-3">
        <Lock className="h-3 w-3" />
        {(confidence * 100).toFixed(0)}%
      </span>
    );
  }

  const isAbove = confidence >= targetConfidence;
  const bgClass = isAbove
    ? "bg-chart-3/10 border-chart-3/30 text-chart-3"
    : confidence >= 0.7
      ? "bg-chart-4/10 border-chart-4/30 text-chart-4"
      : "bg-destructive/10 border-destructive/30 text-destructive";

  return (
    <span
      className={`inline-flex h-8 w-14 items-center justify-center rounded-md border text-xs font-semibold ${bgClass}`}
    >
      {(confidence * 100).toFixed(0)}%
    </span>
  );
}

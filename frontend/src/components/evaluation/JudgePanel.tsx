"use client";

import { Lightbulb, MessageSquareWarning } from "lucide-react";
import type {
  LoopStatus,
  RoundRule,
  TicketTrajectory,
} from "@/hooks/useGroundTruthSSE";

interface JudgePanelProps {
  roundRules: RoundRule[];
  accumulatedRules: string[];
  tickets: TicketTrajectory[];
  status: LoopStatus;
}

export function JudgePanel({
  roundRules,
  accumulatedRules,
  tickets,
  status,
}: JudgePanelProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <Lightbulb className="h-4 w-4 text-chart-4" />
          Regles du juge
          <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {accumulatedRules.length}
          </span>
        </h3>
        <div className="max-h-[180px] space-y-3 overflow-y-auto pr-1">
          {roundRules.map((rr) => (
            <div key={rr.round}>
              <p className="mb-1.5 text-xs font-semibold text-muted-foreground">
                Round {rr.round}
              </p>
              {rr.rules_added.map((rule, idx) => (
                <div
                  key={`add-${idx}`}
                  className="mb-1.5 rounded-md border border-chart-3/20 bg-chart-3/5 px-3 py-2 text-xs leading-relaxed text-foreground"
                >
                  {rule}
                </div>
              ))}
              {rr.rules_modified.map((mod, idx) => (
                <div
                  key={`mod-${idx}`}
                  className="mb-1.5 rounded-md border border-chart-4/20 bg-chart-4/5 px-3 py-2 text-xs leading-relaxed text-foreground"
                >
                  <span className="line-through opacity-50">
                    {mod.old_rule}
                  </span>
                  <br />
                  {mod.new_rule}
                </div>
              ))}
            </div>
          ))}
          {roundRules.length === 0 && status === "running" && (
            <p className="text-xs text-muted-foreground">
              En attente du premier round...
            </p>
          )}
        </div>
      </div>

      {roundRules.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <MessageSquareWarning className="h-4 w-4 text-secondary" />
            Analyse du juge
          </h3>
          <div className="max-h-[180px] space-y-2 overflow-y-auto pr-1">
            {roundRules.at(-1)?.diagnosis && (
              <p className="mb-2 rounded-md border border-secondary/20 bg-secondary/5 px-3 py-2 text-xs leading-relaxed text-foreground">
                {roundRules.at(-1)?.diagnosis}
              </p>
            )}
            {(roundRules.at(-1)?.ticket_evaluations ?? []).map((te) => {
              const ticket = tickets.find(
                (t) => t.classification_id === te.classification_id
              );
              return (
                <div
                  key={te.classification_id}
                  className="rounded-md border border-border bg-muted/30 px-3 py-2"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span className="truncate text-xs font-medium">
                      {ticket?.original_text?.slice(0, 40) ??
                        te.classification_id.slice(0, 8)}
                      ...
                    </span>
                    {!te.meaning_preserved && (
                      <span className="shrink-0 rounded-full bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">
                        sens altere
                      </span>
                    )}
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {te.confidence_analysis}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

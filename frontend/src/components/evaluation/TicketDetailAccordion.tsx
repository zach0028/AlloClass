"use client";

import { AlertTriangle, ChevronDown, ChevronUp, Lock } from "lucide-react";
import type { TicketTrajectory } from "@/hooks/useGroundTruthSSE";

interface TicketDetailAccordionProps {
  tickets: TicketTrajectory[];
  targetConfidence: number;
  expandedTicket: string | null;
  onToggle: (id: string) => void;
}

export function TicketDetailAccordion({
  tickets,
  targetConfidence,
  expandedTicket,
  onToggle,
}: TicketDetailAccordionProps) {
  return (
    <div className="rounded-xl border border-border bg-card shadow-sm">
      <div className="border-b border-border px-6 py-4">
        <h3 className="text-sm font-semibold">Detail par ticket</h3>
      </div>
      <div className="divide-y divide-border">
        {tickets.map((t) => {
          const lastConf = t.confidences.at(-1) ?? 0;
          const isAbove = lastConf >= targetConfidence;
          const isExpanded = expandedTicket === t.classification_id;

          return (
            <div key={t.classification_id}>
              <button
                onClick={() => onToggle(t.classification_id)}
                className="flex w-full items-center gap-4 px-6 py-4 text-left transition-colors hover:bg-accent/50"
              >
                <span
                  className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                    isAbove
                      ? "bg-chart-3/10 text-chart-3"
                      : "bg-destructive/10 text-destructive"
                  }`}
                >
                  {(lastConf * 100).toFixed(0)}%
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {t.original_text}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {t.original_confidence
                      ? `${(t.original_confidence * 100).toFixed(0)}%`
                      : "?"}
                    {t.confidences.map((c, i) => (
                      <span key={i}> → {(c * 100).toFixed(0)}%</span>
                    ))}
                  </p>
                </div>
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                )}
              </button>

              {isExpanded && (
                <div className="border-t border-border bg-muted/30 px-6 py-4">
                  <div className="space-y-3">
                    {t.reformulations.map((reform, rIdx) => (
                      <div
                        key={rIdx}
                        className="rounded-md border border-border bg-card p-3"
                      >
                        <div className="mb-1.5 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-muted-foreground">
                              Round {rIdx + 1}
                            </span>
                            {t.frozen[rIdx] && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-chart-3/10 px-1.5 py-0.5 text-[10px] font-medium text-chart-3">
                                <Lock className="h-3 w-3" />
                                gele
                              </span>
                            )}
                            {t.used_fallbacks[rIdx] && !t.frozen[rIdx] && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-chart-4/10 px-1.5 py-0.5 text-[10px] font-medium text-chart-4">
                                <AlertTriangle className="h-3 w-3" />
                                non reformule
                              </span>
                            )}
                            {t.errors[rIdx] && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">
                                <AlertTriangle className="h-3 w-3" />
                                erreur
                              </span>
                            )}
                          </div>
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                              (t.confidences[rIdx] ?? 0) >= targetConfidence
                                ? "bg-chart-3/10 text-chart-3"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {((t.confidences[rIdx] ?? 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                        {t.errors[rIdx] ? (
                          <p className="text-sm text-destructive">
                            {t.errors[rIdx]}
                          </p>
                        ) : (
                          <p className="text-sm leading-relaxed">{reform}</p>
                        )}
                        {t.results_per_axis[rIdx] &&
                          t.results_per_axis[rIdx].length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {t.results_per_axis[rIdx].map((r) => (
                                <span
                                  key={r.axis_name}
                                  className="rounded-full border border-border bg-background px-2 py-0.5 text-xs"
                                >
                                  {r.axis_name}: {r.category_name}
                                </span>
                              ))}
                            </div>
                          )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

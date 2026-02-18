"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { GeneratedTicketResponse } from "@/types/api";
import { Clock, CheckCircle2, AlertTriangle, X, Trash2, Loader2, ChevronDown, ChevronRight } from "lucide-react";

interface DripFeedMonitorProps {
  newTickets?: GeneratedTicketResponse[];
  onTicketsDeleted?: (deletedIds: string[]) => void;
}

export function DripFeedMonitor({ newTickets = [], onTicketsDeleted }: DripFeedMonitorProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const allTickets = newTickets.slice(0, 100);

  useEffect(() => {
    if (scrollRef.current && allTickets.length > 0) {
      scrollRef.current.scrollTop = 0;
    }
  }, [allTickets.length]);

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const deleteOneMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiFetch(`/api/backoffice/tickets/${id}`, { method: "DELETE" });
      return id;
    },
    onSuccess: (id) => {
      onTicketsDeleted?.([id]);
    },
  });

  const deleteAllMutation = useMutation({
    mutationFn: async (ids: string[]) => {
      await apiFetch("/api/backoffice/tickets/delete-batch", {
        method: "POST",
        body: JSON.stringify({ ids }),
      });
      return ids;
    },
    onSuccess: (ids) => {
      onTicketsDeleted?.(ids);
    },
  });

  const handleDeleteAll = () => {
    const ids = allTickets.map((t) => t.id);
    if (ids.length > 0) {
      deleteAllMutation.mutate(ids);
    }
  };

  const formatTimestamp = (isoDate?: string) => {
    const date = isoDate ? new Date(isoDate) : new Date();
    return date.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const truncateText = (text: string, maxLength: number = 80) => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength) + "...";
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-chart-3";
    if (confidence >= 0.6) return "text-chart-4";
    return "text-destructive";
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 0.8) return "bg-chart-3/10 border-chart-3/20";
    if (confidence >= 0.6) return "bg-chart-4/10 border-chart-4/20";
    return "bg-destructive/10 border-destructive/20";
  };

  const isDeleting = deleteAllMutation.isPending;
  const needsTruncation = (text: string) => text.length > 80;

  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center gap-2 border-b border-border p-4">
        <Clock className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Flux de generation</h2>
        {allTickets.length > 0 && (
          <>
            <span className="ml-auto rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {allTickets.length} tickets
            </span>
            <button
              onClick={handleDeleteAll}
              disabled={isDeleting}
              className="rounded-lg border border-destructive/20 bg-destructive/5 px-2.5 py-1 text-xs font-medium text-destructive transition-colors hover:bg-destructive/10 disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <span className="flex items-center gap-1">
                  <Trash2 className="h-3 w-3" />
                  Tout supprimer
                </span>
              )}
            </button>
          </>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        {allTickets.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-3 rounded-full bg-muted p-4">
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">Aucun ticket genere</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Les tickets generes apparaitront ici en temps reel
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {allTickets.map((ticket, index) => {
              const isExpanded = expandedIds.has(ticket.id);
              const canExpand = needsTruncation(ticket.input_text);

              return (
                <div
                  key={`${ticket.id}-${index}`}
                  className="group relative rounded-lg border border-border bg-background p-4 transition-all hover:border-primary/30 hover:shadow-sm"
                >
                  <button
                    onClick={() => deleteOneMutation.mutate(ticket.id)}
                    disabled={deleteOneMutation.isPending}
                    className="absolute right-2 top-2 rounded-md p-1 text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>

                  <div className="mb-2 flex items-start justify-between gap-3 pr-6">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{formatTimestamp(ticket.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {ticket.was_challenged && (
                        <div className="rounded-full bg-chart-4/10 px-2 py-0.5 text-xs font-medium text-chart-4">
                          <AlertTriangle className="mr-1 inline-block h-3 w-3" />
                          Challenge
                        </div>
                      )}
                      <div
                        className={`rounded-full border px-2 py-0.5 text-xs font-medium ${getConfidenceBg(
                          ticket.overall_confidence
                        )} ${getConfidenceColor(ticket.overall_confidence)}`}
                      >
                        {(ticket.overall_confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <p className="text-sm leading-relaxed text-foreground">
                    {isExpanded ? ticket.input_text : truncateText(ticket.input_text)}
                  </p>

                  {canExpand && (
                    <button
                      onClick={() => toggleExpand(ticket.id)}
                      className="mt-2 flex items-center gap-1 text-xs font-medium text-primary transition-colors hover:text-primary/80"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronDown className="h-3 w-3" />
                          Reduire
                        </>
                      ) : (
                        <>
                          <ChevronRight className="h-3 w-3" />
                          Voir tout
                        </>
                      )}
                    </button>
                  )}

                  {ticket.overall_confidence >= 0.8 && !ticket.was_challenged && !isExpanded && (
                    <div className="mt-2 flex items-center gap-1 text-xs text-chart-3">
                      <CheckCircle2 className="h-3 w-3" />
                      <span>Confiance elevee</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {allTickets.length > 0 && (
        <div className="border-t border-border bg-muted/30 px-4 py-2 text-center text-xs text-muted-foreground">
          Affichage des {allTickets.length} derniers tickets
        </div>
      )}
    </div>
  );
}

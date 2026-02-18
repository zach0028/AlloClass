"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { GeneratorControls } from "@/components/backoffice/GeneratorControls";
import { DripFeedMonitor } from "@/components/backoffice/DripFeedMonitor";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { ClassificationListResponse, GeneratedTicketResponse } from "@/types/api";

export default function BackofficePage() {
  const [newTickets, setNewTickets] = useState<GeneratedTicketResponse[]>([]);
  const { currentConfigId } = useConfigStore();
  const queryClient = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ["classifications", "backoffice", currentConfigId],
    queryFn: () =>
      apiFetch<ClassificationListResponse>(
        `/api/classifications?config_id=${currentConfigId}&page=1&page_size=100&min_confidence=0&max_confidence=1`
      ),
    enabled: !!currentConfigId,
  });

  const allTickets = useMemo(() => {
    const newIds = new Set(newTickets.map((t) => t.id));
    const fromDb: GeneratedTicketResponse[] = (existing?.items ?? [])
      .filter((c) => !newIds.has(c.id))
      .map((c) => ({
        id: c.id,
        input_text: c.input_text,
        overall_confidence: c.overall_confidence,
        was_challenged: c.was_challenged,
        created_at: c.created_at,
      }));
    return [...newTickets, ...fromDb];
  }, [newTickets, existing]);

  const handleTicketsGenerated = (tickets: GeneratedTicketResponse[]) => {
    setNewTickets((prev) => [...tickets, ...prev]);
    queryClient.invalidateQueries({ queryKey: ["classifications", "backoffice"] });
  };

  const handleTicketsDeleted = (deletedIds: string[]) => {
    const idSet = new Set(deletedIds);
    setNewTickets((prev) => prev.filter((t) => !idSet.has(t.id)));
    queryClient.invalidateQueries({ queryKey: ["classifications", "backoffice"] });
  };

  return (
    <div className="h-screen overflow-hidden bg-background p-6">
      <h1 className="mb-6 text-2xl font-bold text-foreground">Backoffice</h1>

      <div className="flex flex-1 gap-6" style={{ height: "calc(100% - 60px)" }}>
        <div className="w-[480px] shrink-0">
          <GeneratorControls onTicketsGenerated={handleTicketsGenerated} />
        </div>

        <div className="flex-1">
          <DripFeedMonitor newTickets={allTickets} onTicketsDeleted={handleTicketsDeleted} />
        </div>
      </div>
    </div>
  );
}

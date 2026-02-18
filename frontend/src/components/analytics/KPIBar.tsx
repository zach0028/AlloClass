"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Target, AlertCircle, MessageSquare } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { KPIResponse } from "@/types/api";

export function KPIBar() {
  const { currentConfigId } = useConfigStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-kpis", currentConfigId],
    queryFn: () =>
      apiFetch<KPIResponse>(
        `/api/analytics/kpis?config_id=${currentConfigId}`
      ),
    enabled: !!currentConfigId,
  });

  if (!currentConfigId) {
    return (
      <div className="col-span-full text-center py-8 text-muted-foreground">
        Sélectionnez une configuration pour voir les métriques
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="col-span-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="bg-card border border-border rounded-xl p-6 animate-pulse"
          >
            <div className="h-10 w-10 bg-muted rounded-lg mb-4" />
            <div className="h-8 bg-muted rounded mb-2" />
            <div className="h-4 bg-muted rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="col-span-full bg-destructive/10 border border-destructive/20 rounded-xl p-6 text-destructive">
        Erreur de chargement des KPIs
      </div>
    );
  }

  if (!data) return null;

  const kpis = [
    {
      icon: Activity,
      value: data.total_classifications.toLocaleString(),
      label: "Classifications totales",
      color: "text-chart-1",
      bgColor: "bg-chart-1/10",
    },
    {
      icon: Target,
      value: `${(data.average_confidence * 100).toFixed(1)}%`,
      label: "Confiance moyenne",
      color: "text-chart-2",
      bgColor: "bg-chart-2/10",
    },
    {
      icon: AlertCircle,
      value: `${(data.challenge_rate * 100).toFixed(1)}%`,
      label: "Taux de challenge",
      color: "text-chart-4",
      bgColor: "bg-chart-4/10",
    },
    {
      icon: MessageSquare,
      value: data.feedback_count.toLocaleString(),
      label: "Feedbacks reçus",
      color: "text-chart-3",
      bgColor: "bg-chart-3/10",
    },
  ];

  return (
    <>
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <div
            key={kpi.label}
            className="bg-card border border-border rounded-xl shadow-sm p-6"
          >
            <div className={`${kpi.bgColor} ${kpi.color} w-10 h-10 rounded-lg flex items-center justify-center mb-4`}>
              <Icon className="w-5 h-5" />
            </div>
            <div className="text-3xl font-bold mb-1">{kpi.value}</div>
            <div className="text-sm text-muted-foreground">{kpi.label}</div>
          </div>
        );
      })}
    </>
  );
}

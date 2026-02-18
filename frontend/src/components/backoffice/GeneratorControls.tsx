"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type {
  GeneratedTicketResponse,
  DripFeedStatusResponse,
  ScenarioResponse,
} from "@/types/api";
import {
  Zap,
  Play,
  StopCircle,
  Loader2,
  Sun,
  Truck,
  Tag,
  Crown,
  FlaskConical,
} from "lucide-react";

type DeliveryMode = "batch" | "drip-feed";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  sun: Sun,
  truck: Truck,
  tag: Tag,
  crown: Crown,
  flask: FlaskConical,
  zap: Zap,
};

interface GeneratorControlsProps {
  onTicketsGenerated?: (tickets: GeneratedTicketResponse[]) => void;
}

export function GeneratorControls({ onTicketsGenerated }: GeneratorControlsProps) {
  const { currentConfigId } = useConfigStore();
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [deliveryMode, setDeliveryMode] = useState<DeliveryMode>("batch");
  const [batchCount, setBatchCount] = useState(10);
  const [dripInterval, setDripInterval] = useState(5);
  const [dripTotal, setDripTotal] = useState(50);

  const { data: scenarios = [] } = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => apiFetch<ScenarioResponse[]>("/api/backoffice/scenarios"),
  });

  const { data: dripStatus, refetch: refetchStatus } = useQuery({
    queryKey: ["drip-feed-status"],
    queryFn: () => apiFetch<DripFeedStatusResponse>("/api/backoffice/status"),
    refetchInterval: 2000,
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      return apiFetch<GeneratedTicketResponse[]>("/api/backoffice/generate", {
        method: "POST",
        body: JSON.stringify({
          config_id: currentConfigId,
          count: batchCount,
          scenario_id: selectedScenario,
        }),
      });
    },
    onSuccess: (data) => {
      onTicketsGenerated?.(data);
    },
  });

  const startDripMutation = useMutation({
    mutationFn: async () => {
      return apiFetch("/api/backoffice/drip-feed/start", {
        method: "POST",
        body: JSON.stringify({
          config_id: currentConfigId,
          interval_seconds: dripInterval,
          total_count: dripTotal,
          scenario_id: selectedScenario,
        }),
      });
    },
    onSuccess: () => {
      refetchStatus();
    },
  });

  const stopDripMutation = useMutation({
    mutationFn: async () => {
      return apiFetch("/api/backoffice/drip-feed/stop", { method: "POST" });
    },
    onSuccess: () => {
      refetchStatus();
    },
  });

  const handleGenerate = () => {
    if (!currentConfigId || !selectedScenario) return;
    generateMutation.mutate();
  };

  const handleStartDrip = () => {
    if (!currentConfigId || !selectedScenario) return;
    startDripMutation.mutate();
  };

  const isDisabled = !currentConfigId;
  const isGenerating = generateMutation.isPending;
  const isDripRunning = dripStatus?.is_running ?? false;
  const activeScenario = scenarios.find((s) => s.id === selectedScenario);
  const isAdversarial = activeScenario?.strategy === "adversarial";

  return (
    <div className="flex h-full flex-col rounded-xl border border-border bg-card shadow-sm">
      <div className="flex items-center gap-2 border-b border-border p-6 pb-4">
        <Zap className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">Generateur de tickets</h2>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-6 pt-4">
        {/* Scenario Cards */}
        <div>
          <label className="mb-3 block text-sm font-medium">Scenario</label>
          <div className="grid grid-cols-1 gap-2">
            {scenarios.map((scenario) => {
              const Icon = ICON_MAP[scenario.icon] || Zap;
              const isSelected = selectedScenario === scenario.id;
              return (
                <button
                  key={scenario.id}
                  onClick={() => setSelectedScenario(scenario.id)}
                  disabled={isDisabled || isDripRunning}
                  className={`flex items-start gap-3 rounded-lg border-2 px-4 py-3 text-left transition-all ${
                    isSelected
                      ? "border-primary bg-primary/5"
                      : "border-border bg-background hover:border-primary/40"
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  <div
                    className={`mt-0.5 rounded-lg p-1.5 ${
                      isSelected
                        ? "bg-primary/10 text-primary"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-medium ${
                          isSelected ? "text-primary" : "text-foreground"
                        }`}
                      >
                        {scenario.name}
                      </span>
                      {scenario.difficulty_bias === "hard" && (
                        <span className="rounded-full bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">
                          difficile
                        </span>
                      )}
                      {scenario.strategy === "adversarial" && (
                        <span className="rounded-full bg-chart-4/10 px-1.5 py-0.5 text-[10px] font-medium text-chart-4">
                          cas piege
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {scenario.description}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Delivery Mode Toggle */}
        {selectedScenario && !isAdversarial && (
          <div>
            <label className="mb-3 block text-sm font-medium">Mode de livraison</label>
            <div className="grid grid-cols-2 gap-2">
              {(["batch", "drip-feed"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setDeliveryMode(m)}
                  disabled={isDisabled || isDripRunning}
                  className={`rounded-lg border-2 px-4 py-2.5 text-sm font-medium transition-all ${
                    deliveryMode === m
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border bg-background text-foreground hover:border-primary/50"
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  {m === "batch" ? "Tous d'un coup" : "Au fil de l'eau"}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Batch Controls */}
        {selectedScenario && (deliveryMode === "batch" || isAdversarial) && (
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium">Nombre de tickets</label>
              <input
                type="number"
                min={1}
                max={200}
                value={batchCount}
                onChange={(e) => setBatchCount(parseInt(e.target.value) || 1)}
                disabled={isDisabled}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <button
              onClick={handleGenerate}
              disabled={isDisabled || isGenerating}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generation en cours...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Generer {batchCount} tickets
                </>
              )}
            </button>
          </div>
        )}

        {/* Drip-feed Controls */}
        {selectedScenario && deliveryMode === "drip-feed" && !isAdversarial && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-2 block text-sm font-medium">Intervalle (s)</label>
                <input
                  type="number"
                  min={1}
                  max={3600}
                  value={dripInterval}
                  onChange={(e) => setDripInterval(parseInt(e.target.value) || 1)}
                  disabled={isDisabled || isDripRunning}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label className="mb-2 block text-sm font-medium">Total</label>
                <input
                  type="number"
                  min={1}
                  max={1000}
                  value={dripTotal}
                  onChange={(e) => setDripTotal(parseInt(e.target.value) || 1)}
                  disabled={isDisabled || isDripRunning}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>

            {isDripRunning && dripStatus && (
              <div className="rounded-lg bg-muted p-4">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-medium">Progression</span>
                  <span className="text-muted-foreground">
                    {dripStatus.generated_count} / {dripStatus.total_count}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-background">
                  <div
                    className="h-full bg-primary transition-all duration-500"
                    style={{
                      width: `${(dripStatus.generated_count / dripStatus.total_count) * 100}%`,
                    }}
                  />
                </div>
              </div>
            )}

            <div className="flex gap-3">
              {!isDripRunning ? (
                <button
                  onClick={handleStartDrip}
                  disabled={isDisabled || startDripMutation.isPending}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {startDripMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Demarrage...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Demarrer
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={() => stopDripMutation.mutate()}
                  disabled={stopDripMutation.isPending}
                  className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-destructive px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {stopDripMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Arret...
                    </>
                  ) : (
                    <>
                      <StopCircle className="h-4 w-4" />
                      Arreter
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}

        {!selectedScenario && !isDisabled && (
          <div className="rounded-lg border border-dashed border-border bg-muted/30 p-6 text-center">
            <p className="text-sm text-muted-foreground">
              Selectionnez un scenario pour commencer
            </p>
          </div>
        )}

        {!currentConfigId && (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
            <p className="text-sm text-destructive">
              Veuillez selectionner une configuration pour continuer.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

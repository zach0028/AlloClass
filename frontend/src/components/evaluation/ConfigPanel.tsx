"use client";

import { useState } from "react";
import { FlaskConical, Zap } from "lucide-react";
import type { GroundTruthConfig } from "@/hooks/useGroundTruthSSE";

interface ConfigPanelProps {
  disabled: boolean;
  onLaunch: (config: GroundTruthConfig) => void;
}

export function ConfigPanel({ disabled, onLaunch }: ConfigPanelProps) {
  const [ticketCount, setTicketCount] = useState(5);
  const [mode, setMode] = useState<"rounds" | "threshold">("rounds");
  const [maxRounds, setMaxRounds] = useState(5);
  const [targetConfidence, setTargetConfidence] = useState(90);

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div className="rounded-lg bg-primary/10 p-2 text-primary">
          <FlaskConical className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Ground truth iteratif</h2>
          <p className="text-xs text-muted-foreground">
            Boucle d&apos;auto-amelioration : generateur adaptatif + juge
          </p>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-sm font-medium">
            Tickets a tester
          </label>
          <input
            type="number"
            min={1}
            max={100}
            value={ticketCount}
            onChange={(e) => setTicketCount(Number(e.target.value))}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
          />
          <p className="mt-1 text-xs text-muted-foreground">
            Les tickets les moins confiants seront selectionnes
          </p>
        </div>

        <div>
          <label className="mb-1.5 block text-sm font-medium">Mode</label>
          <div className="flex gap-2">
            <button
              onClick={() => setMode("rounds")}
              className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-all ${
                mode === "rounds"
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-transparent text-muted-foreground hover:border-muted-foreground/30"
              }`}
            >
              Rounds fixes
            </button>
            <button
              onClick={() => setMode("threshold")}
              className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium transition-all ${
                mode === "threshold"
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border bg-transparent text-muted-foreground hover:border-muted-foreground/30"
              }`}
            >
              Seuil cible
            </button>
          </div>
        </div>

        {mode === "rounds" && (
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Nombre de rounds
            </label>
            <input
              type="number"
              min={1}
              max={15}
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
            />
          </div>
        )}

        <div>
          <label className="mb-1.5 block text-sm font-medium">
            Confiance cible
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={50}
              max={100}
              value={targetConfidence}
              onChange={(e) => setTargetConfidence(Number(e.target.value))}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
            />
            <span className="text-sm text-muted-foreground">%</span>
          </div>
        </div>
      </div>

      <div className="mt-6">
        <button
          onClick={() =>
            onLaunch({ ticketCount, mode, maxRounds, targetConfidence })
          }
          disabled={disabled}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
        >
          <Zap className="h-4 w-4" />
          Lancer la boucle
        </button>
      </div>
    </div>
  );
}

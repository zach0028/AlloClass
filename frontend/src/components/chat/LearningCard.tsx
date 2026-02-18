"use client";

import { useState } from "react";
import { Database, BookOpen, SlidersHorizontal, Check, Loader2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { LearningCard as LearningCardType } from "@/hooks/useChat";

interface LearningCardProps {
  card: LearningCardType;
}

const LEVELS = [
  {
    key: "level_1" as const,
    icon: Database,
    title: "Few-shot immediat",
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-200",
  },
  {
    key: "level_2" as const,
    icon: BookOpen,
    title: "Regle detectee",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
  },
  {
    key: "level_3" as const,
    icon: SlidersHorizontal,
    title: "Seuils adaptatifs",
    color: "text-purple-600",
    bg: "bg-purple-50",
    border: "border-purple-200",
  },
];

export function LearningCard({ card }: LearningCardProps) {
  const [ruleValidated, setRuleValidated] = useState(false);
  const [ruleLoading, setRuleLoading] = useState(false);
  const { currentConfigId } = useConfigStore();

  const activeLevels = LEVELS.filter((l) => card[l.key]?.active);

  if (activeLevels.length === 0) return null;

  const handleValidateRule = async () => {
    const proposed = card.level_2?.proposed_rule;
    if (!proposed || !currentConfigId) return;

    setRuleLoading(true);
    try {
      await apiFetch("/api/learned-rules", {
        method: "POST",
        body: JSON.stringify({
          config_id: currentConfigId,
          axis_id: proposed.axis_id ?? null,
          rule_text: proposed.proposed_rule_text ?? proposed.rule_text ?? "",
          source_feedback_count: proposed.source_feedback_count ?? 0,
        }),
      });
      setRuleValidated(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("409") || msg.includes("existe deja")) {
        setRuleValidated(true);
      }
    } finally {
      setRuleLoading(false);
    }
  };

  return (
    <div className="w-full rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm font-semibold">Ce que j&apos;apprends</span>
      </div>

      <div className="flex flex-col gap-2">
        {activeLevels.map((level) => {
          const Icon = level.icon;
          const data = card[level.key];
          return (
            <div
              key={level.key}
              className={`rounded-lg border ${level.border} ${level.bg} px-3 py-2.5`}
            >
              <div className="flex items-start gap-2">
                <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${level.color}`} />
                <div className="min-w-0 flex-1">
                  <span className={`text-xs font-semibold ${level.color}`}>
                    {level.title}
                  </span>
                  <p className="mt-0.5 text-xs leading-relaxed text-foreground/80">
                    {data.message}
                  </p>
                  {level.key === "level_2" && data.proposed_rule && (
                    <div className="mt-2">
                      {ruleValidated ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-600">
                          <Check className="h-3.5 w-3.5" />
                          Regle validee et activee
                        </span>
                      ) : (
                        <button
                          onClick={handleValidateRule}
                          disabled={ruleLoading}
                          className="inline-flex items-center gap-1.5 rounded-md border border-amber-300 bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-200 disabled:opacity-50"
                        >
                          {ruleLoading ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Check className="h-3 w-3" />
                          )}
                          Valider cette regle
                        </button>
                      )}
                    </div>
                  )}
                  {data.calibration_warning && (
                    <p className="mt-1 text-xs font-medium text-red-600">
                      {data.calibration_warning}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

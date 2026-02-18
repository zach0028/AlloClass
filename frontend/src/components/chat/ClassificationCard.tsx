"use client";

import { Shield, ShieldAlert } from "lucide-react";
import { confidenceTextColor, confidenceBarColor } from "@/lib/confidence";

interface AxisResult {
  axis_name: string;
  category_name: string;
  confidence: number;
  reasoning?: string;
}

interface ClassificationCardProps {
  data: Record<string, unknown>;
}

export function ClassificationCard({ data }: ClassificationCardProps) {
  const results = (data.results ?? []) as AxisResult[];
  const overall = (data.overall_confidence ?? 0) as number;
  const wasChallenged = data.was_challenged as boolean;

  if (results.length === 0) return null;

  return (
    <div className="w-full rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {wasChallenged ? (
            <ShieldAlert className="h-4 w-4 text-yellow-500" />
          ) : (
            <Shield className="h-4 w-4 text-primary" />
          )}
          <span className="text-sm font-semibold">Classification</span>
        </div>
        <span className={`text-sm font-medium ${confidenceTextColor(overall)}`}>
          {Math.round(overall * 100)}%
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {results.map((r) => (
          <div key={r.axis_name} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs text-muted-foreground truncate">
              {r.axis_name}
            </span>
            <div className="flex flex-1 items-center gap-2">
              <div className="h-1.5 flex-1 rounded-full bg-muted">
                <div
                  className={`h-full rounded-full transition-all ${confidenceBarColor(r.confidence)}`}
                  style={{ width: `${r.confidence * 100}%` }}
                />
              </div>
              <span className="w-20 text-xs font-medium truncate">{r.category_name}</span>
              <span className={`w-10 text-right text-xs ${confidenceTextColor(r.confidence)}`}>
                {Math.round(r.confidence * 100)}%
              </span>
            </div>
          </div>
        ))}
      </div>

      {wasChallenged && (
        <div className="mt-3 rounded-lg bg-yellow-50 px-3 py-2 text-xs text-yellow-700">
          Le Challenger a conteste certains axes
        </div>
      )}
    </div>
  );
}

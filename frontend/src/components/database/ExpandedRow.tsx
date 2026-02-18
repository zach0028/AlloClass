"use client";

import { Clock, Cpu, Zap, AlertTriangle } from "lucide-react";
import type {
  ClassificationResponse,
  AxisResultDetail,
  ChallengerDetail,
} from "@/types/api";
import { confidenceTextColor, confidenceBarColor } from "@/lib/confidence";

interface ExpandedRowProps {
  classification: ClassificationResponse;
}

function AxisDetail({ result }: { result: AxisResultDetail }) {
  const confidence = result.confidence * 100;

  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h4 className="text-sm font-semibold text-foreground">
            {result.axis_name}
          </h4>
          <p className="mt-1 text-base font-medium text-primary">
            {result.category_name}
          </p>
        </div>
        <div className="text-right">
          <div
            className={`text-lg font-bold ${confidenceTextColor(result.confidence)}`}
          >
            {confidence.toFixed(1)}%
          </div>
          <div className="mt-1 h-2 w-24 overflow-hidden rounded-full bg-muted">
            <div
              className={`h-full ${confidenceBarColor(result.confidence)}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      </div>

      {result.all_votes && new Set(result.all_votes).size > 1 && (
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">
            Distribution des votes
          </p>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(
              result.all_votes.reduce<Record<string, number>>((acc, v) => {
                acc[v] = (acc[v] ?? 0) + 1;
                return acc;
              }, {})
            )
              .sort(([, a], [, b]) => b - a)
              .map(([category, count]) => (
                <span
                  key={category}
                  className={`rounded-md px-2 py-1 text-xs font-medium ${
                    category === result.category_name
                      ? "bg-primary/10 text-primary"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {category}: {count}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ChallengerSection({
  original,
  challenger,
}: {
  original: AxisResultDetail;
  challenger: ChallengerDetail;
}) {
  const originalConfidence = challenger.original_confidence * 100;

  return (
    <div className="rounded-lg border-2 border-yellow-500/30 bg-yellow-50/50 p-4">
      <div className="mb-3 flex items-center gap-2 text-yellow-700">
        <AlertTriangle className="h-4 w-4" />
        <h4 className="text-sm font-semibold">{challenger.axis_name}</h4>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-white p-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Classification originale
          </p>
          <p className="text-sm font-semibold text-foreground">
            {original.category_name}
          </p>
          <div className="mt-1 text-xs text-muted-foreground">
            Confiance: {originalConfidence.toFixed(1)}%
          </div>
        </div>

        <div className="rounded-lg border border-yellow-500 bg-white p-3">
          <p className="mb-2 text-xs font-medium text-yellow-700">
            Alternative proposée
          </p>
          <p className="text-sm font-semibold text-yellow-700">
            {challenger.alternative_category}
          </p>
          <div className="mt-2 text-xs text-muted-foreground">
            {challenger.argument}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ExpandedRow({ classification }: ExpandedRowProps) {
  return (
    <div className="border-t border-border bg-accent/30 p-6">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 rounded-lg border border-border bg-card p-4">
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Texte du ticket
          </h3>
          <p className="text-sm leading-relaxed text-foreground">
            {classification.input_text}
          </p>
        </div>

        <div className="mb-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">
            Résultats par axe
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {classification.results.map((result) => (
              <AxisDetail key={result.axis_id} result={result} />
            ))}
          </div>
        </div>

        {classification.was_challenged &&
          classification.challenger_response &&
          classification.challenger_response.length > 0 && (
            <div className="mb-6">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                Classifications challengées
              </h3>
              <div className="space-y-4">
                {classification.challenger_response.map((challenger, i) => {
                  const original = classification.results.find(
                    (r) => r.axis_id === challenger.axis_id
                  );
                  if (!original) return null;
                  return (
                    <ChallengerSection
                      key={challenger.axis_id ?? i}
                      original={original}
                      challenger={challenger}
                    />
                  );
                })}
              </div>
            </div>
          )}

        <div className="rounded-lg border border-border bg-muted/30 p-4">
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Métadonnées
          </h3>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="flex items-center gap-2 text-sm">
              <Cpu className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-foreground">
                {classification.model_used}
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {classification.tokens_used.toLocaleString()} tokens
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {classification.processing_time_ms}ms
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

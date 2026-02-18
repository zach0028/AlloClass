"use client";

import { GroundTruthLoop } from "@/components/evaluation/GroundTruthLoop";

export default function EvaluationPage() {
  return (
    <div className="h-screen overflow-y-auto bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-8">
        <h1 className="text-2xl font-bold text-foreground">Evaluation</h1>
        <GroundTruthLoop />
      </div>
    </div>
  );
}

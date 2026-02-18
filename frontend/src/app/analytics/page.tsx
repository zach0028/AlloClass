"use client";

import { KPIBar } from "@/components/analytics/KPIBar";
import { ConfidenceHistogram } from "@/components/analytics/ConfidenceHistogram";
import { EmbeddingMap } from "@/components/analytics/EmbeddingMap";

export default function AnalyticsPage() {
  return (
    <div className="h-screen overflow-auto bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPIBar />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ConfidenceHistogram />
          <EmbeddingMap />
        </div>
      </div>
    </div>
  );
}

"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { ConfidenceBucket } from "@/types/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function ConfidenceHistogram() {
  const { currentConfigId } = useConfigStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-confidence", currentConfigId],
    queryFn: () =>
      apiFetch<{ buckets: ConfidenceBucket[] }>(
        `/api/analytics/confidence?config_id=${currentConfigId}`
      ),
    enabled: !!currentConfigId,
  });

  if (!currentConfigId || isLoading) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm p-6">
        <h3 className="text-sm font-semibold mb-4">Distribution de confiance</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-sm text-muted-foreground">Chargement...</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-card border border-border rounded-xl shadow-sm p-6">
        <h3 className="text-sm font-semibold mb-4">Distribution de confiance</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-sm text-destructive">Erreur de chargement</div>
        </div>
      </div>
    );
  }

  const labels = data.buckets.map(
    (b) => `${(b.range_start * 100).toFixed(0)}-${(b.range_end * 100).toFixed(0)}%`
  );
  const counts = data.buckets.map((b) => b.count);

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm p-6">
      <h3 className="text-sm font-semibold mb-4">Distribution de confiance</h3>
      <Plot
        data={[
          {
            x: labels,
            y: counts,
            type: "bar",
            marker: {
              color: "#9767FF",
              line: { width: 0 },
            },
            hovertemplate: "%{y} classifications<extra></extra>",
          },
        ]}
        layout={{
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { family: "Poppins, sans-serif", size: 12 },
          margin: { t: 20, b: 60, l: 50, r: 20 },
          xaxis: {
            gridcolor: "#D0D6E0",
            showgrid: false,
            zeroline: false,
            title: { text: "Niveau de confiance", standoff: 10 },
          },
          yaxis: {
            gridcolor: "#D0D6E0",
            showgrid: true,
            zeroline: false,
            title: { text: "Nombre", standoff: 10 },
          },
          showlegend: false,
          hovermode: "closest",
        }}
        config={{
          displayModeBar: false,
          responsive: true,
        }}
        className="w-full h-80"
        useResizeHandler
        style={{ width: "100%", height: "320px" }}
      />
    </div>
  );
}

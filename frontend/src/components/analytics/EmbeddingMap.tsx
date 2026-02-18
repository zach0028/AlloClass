"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import type Plotly from "plotly.js";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { ClassificationMatrixResponse } from "@/types/api";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export function EmbeddingMap() {
  const { currentConfigId } = useConfigStore();
  const [xAxis, setXAxis] = useState<string | null>(null);
  const [yAxis, setYAxis] = useState<string | null>(null);

  const xParam = xAxis ? `&x_axis=${encodeURIComponent(xAxis)}` : "";
  const yParam = yAxis ? `&y_axis=${encodeURIComponent(yAxis)}` : "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-matrix", currentConfigId, xAxis, yAxis],
    queryFn: () =>
      apiFetch<ClassificationMatrixResponse>(
        `/api/analytics/classification-matrix?config_id=${currentConfigId}${xParam}${yParam}`
      ),
    enabled: !!currentConfigId,
  });

  if (!currentConfigId || isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h3 className="mb-4 text-sm font-semibold">Matrice de classification</h3>
        <div className="flex h-80 items-center justify-center">
          <div className="text-sm text-muted-foreground">Chargement...</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h3 className="mb-4 text-sm font-semibold">Matrice de classification</h3>
        <div className="flex h-80 items-center justify-center">
          <div className="text-sm text-destructive">Erreur de chargement</div>
        </div>
      </div>
    );
  }

  if (!data.x_axis || !data.y_axis || data.cells.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h3 className="mb-4 text-sm font-semibold">Matrice de classification</h3>
        <div className="flex h-80 items-center justify-center">
          <div className="text-sm text-muted-foreground">
            {data.axes.length < 2
              ? "Minimum 2 axes requis pour la matrice"
              : "Aucune donnee disponible"}
          </div>
        </div>
      </div>
    );
  }

  const xAxisData = data.axes.find((a) => a.name === data.x_axis);
  const yAxisData = data.axes.find((a) => a.name === data.y_axis);
  const xCategories = xAxisData?.categories ?? [];
  const yCategories = yAxisData?.categories ?? [];

  const cellMap = new Map<string, { count: number; avg_confidence: number }>();
  for (const cell of data.cells) {
    cellMap.set(`${cell.x_category}||${cell.y_category}`, {
      count: cell.count,
      avg_confidence: cell.avg_confidence,
    });
  }

  const zValues = yCategories.map((yCat) =>
    xCategories.map((xCat) => cellMap.get(`${xCat}||${yCat}`)?.count ?? 0)
  );

  const hoverText = yCategories.map((yCat) =>
    xCategories.map((xCat) => {
      const cell = cellMap.get(`${xCat}||${yCat}`);
      if (!cell || cell.count === 0) return "Aucun ticket";
      return `${cell.count} ticket${cell.count > 1 ? "s" : ""}<br>Confiance moy. : ${(cell.avg_confidence * 100).toFixed(0)}%`;
    })
  );

  const hasMultipleAxes = data.axes.length > 2;

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Matrice de classification</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Distribution des {data.total} tickets par paire de categories
          </p>
        </div>
      </div>

      {hasMultipleAxes && (
        <div className="mb-4 flex gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted-foreground">Axe X</label>
            <select
              value={data.x_axis}
              onChange={(e) => setXAxis(e.target.value)}
              className="rounded-md border border-input bg-transparent px-2 py-1 text-xs shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
            >
              {data.axes.map((a) => (
                <option key={a.name} value={a.name}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted-foreground">Axe Y</label>
            <select
              value={data.y_axis}
              onChange={(e) => setYAxis(e.target.value)}
              className="rounded-md border border-input bg-transparent px-2 py-1 text-xs shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
            >
              {data.axes.map((a) => (
                <option key={a.name} value={a.name}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <Plot
        data={[
          {
            z: zValues,
            x: xCategories,
            y: yCategories,
            type: "heatmap",
            colorscale: [
              [0, "#F3F0FF"],
              [0.25, "#D4C5FF"],
              [0.5, "#B49AFF"],
              [0.75, "#9767FF"],
              [1, "#7040D9"],
            ],
            hovertemplate: "<b>%{x}</b> × <b>%{y}</b><br>%{z} tickets<extra></extra>",
            showscale: true,
            colorbar: {
              title: { text: "Tickets", side: "right" },
              thickness: 12,
              len: 0.8,
              tickfont: { size: 10, family: "Poppins, sans-serif" },
            },
            zmin: 0,
          } as unknown as Plotly.Data,
        ]}
        layout={
          {
            paper_bgcolor: "transparent",
            plot_bgcolor: "transparent",
            font: { family: "Poppins, sans-serif", size: 12 },
            margin: { t: 10, b: 140, l: 120, r: 60 },
            xaxis: {
              title: { text: data.x_axis, standoff: 15 },
              tickangle: -35,
              tickfont: { size: 11 },
              side: "bottom",
            },
            yaxis: {
              title: { text: data.y_axis, standoff: 10 },
              tickfont: { size: 11 },
              autorange: "reversed",
            },
            annotations: yCategories.flatMap((yCat, yi) =>
              xCategories.map((xCat, xi) => {
                const val = zValues[yi][xi];
                const maxVal = Math.max(...zValues.flat());
                return {
                  x: xCat,
                  y: yCat,
                  text: val > 0 ? String(val) : "",
                  showarrow: false,
                  font: {
                    size: 14,
                    family: "Poppins, sans-serif",
                    color: val > maxVal * 0.5 ? "#FFFFFF" : "#1a1a2e",
                  },
                };
              })
            ),
          } as Partial<Plotly.Layout>
        }
        config={{ displayModeBar: false, responsive: true }}
        className="h-80 w-full"
        useResizeHandler
        style={{ width: "100%", height: "420px" }}
      />
    </div>
  );
}

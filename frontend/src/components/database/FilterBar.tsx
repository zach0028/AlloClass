"use client";

import { Search, Filter } from "lucide-react";

interface FilterBarProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  minConfidence: number;
  onMinConfidenceChange: (value: number) => void;
  maxConfidence: number;
  onMaxConfidenceChange: (value: number) => void;
  challengedFilter: boolean | null;
  onChallengedFilterChange: (value: boolean | null) => void;
  totalCount: number;
}

export function FilterBar({
  searchQuery,
  onSearchChange,
  minConfidence,
  onMinConfidenceChange,
  maxConfidence,
  onMaxConfidenceChange,
  challengedFilter,
  onChallengedFilterChange,
  totalCount,
}: FilterBarProps) {
  return (
    <div className="mb-6 rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="mb-4 flex items-center gap-2 text-sm font-medium text-foreground">
        <Filter className="h-4 w-4" />
        Filtres
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="relative lg:col-span-2">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Rechercher dans les tickets..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-lg border border-input bg-background py-2 pl-10 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground">
            Confiance:
          </label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min="0"
              max="100"
              value={minConfidence}
              onChange={(e) => onMinConfidenceChange(Number(e.target.value))}
              className="w-16 rounded-lg border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <span className="text-muted-foreground">-</span>
            <input
              type="number"
              min="0"
              max="100"
              value={maxConfidence}
              onChange={(e) => onMaxConfidenceChange(Number(e.target.value))}
              className="w-16 rounded-lg border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <span className="text-sm text-muted-foreground">%</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-muted-foreground">
            Challengé:
          </label>
          <select
            value={challengedFilter === null ? "all" : String(challengedFilter)}
            onChange={(e) => {
              const val = e.target.value;
              onChallengedFilterChange(
                val === "all" ? null : val === "true"
              );
            }}
            className="rounded-lg border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">Tous</option>
            <option value="true">Oui</option>
            <option value="false">Non</option>
          </select>
        </div>
      </div>

      <div className="mt-4 border-t border-border pt-3">
        <p className="text-sm font-medium text-muted-foreground">
          <span className="text-lg font-semibold text-foreground">
            {totalCount}
          </span>{" "}
          classification{totalCount !== 1 ? "s" : ""}
        </p>
      </div>
    </div>
  );
}

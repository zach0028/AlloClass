"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, AlertTriangle } from "lucide-react";
import type { ClassificationResponse } from "@/types/api";
import { confidenceTextColor } from "@/lib/confidence";
import { ExpandedRow } from "./ExpandedRow";

interface DataTableProps {
  data: ClassificationResponse[];
  isLoading: boolean;
  currentPage: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div
          key={i}
          className="h-14 animate-pulse rounded-lg bg-muted/50"
        ></div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl border border-border bg-card py-16 text-center shadow-sm">
      <p className="text-sm text-muted-foreground">
        Aucune classification trouvée
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Essayez de modifier vos filtres
      </p>
    </div>
  );
}

export function DataTable({
  data,
  isLoading,
  currentPage,
  pageSize,
  totalItems,
  onPageChange,
}: DataTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const totalPages = Math.ceil(totalItems / pageSize);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const handleRowClick = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <TableSkeleton />
      </div>
    );
  }

  if (data.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="w-10 px-4 py-3"></th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Ticket
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Classifications
                </th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Confiance
                </th>
                <th className="w-16 px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((classification) => {
                const isExpanded = expandedId === classification.id;
                return (
                  <tr key={classification.id}>
                    <td colSpan={6} className="border-b border-border p-0">
                      <button
                        onClick={() => handleRowClick(classification.id)}
                        className="w-full transition-colors hover:bg-accent/50"
                      >
                        <div className="flex items-center">
                          <div className="flex w-10 items-center justify-center px-4 py-4">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                          <div className="flex-1 px-4 py-4 text-left">
                            <p className="max-w-md truncate text-sm text-foreground">
                              {classification.input_text}
                            </p>
                          </div>
                          <div className="px-4 py-4 text-left">
                            <div className="flex flex-wrap gap-1.5">
                              {classification.results.slice(0, 3).map((result) => (
                                <span
                                  key={result.axis_id}
                                  className="rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary"
                                  title={`${result.axis_name}: ${result.category_name}`}
                                >
                                  {result.category_name}
                                </span>
                              ))}
                              {classification.results.length > 3 && (
                                <span className="rounded-md bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">
                                  +{classification.results.length - 3}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="px-4 py-4 text-center">
                            <span
                              className={`text-sm font-semibold ${confidenceTextColor(classification.overall_confidence)}`}
                            >
                              {(classification.overall_confidence * 100).toFixed(
                                1
                              )}
                              %
                            </span>
                          </div>
                          <div className="w-16 px-4 py-4 text-center">
                            {classification.was_challenged && (
                              <AlertTriangle className="inline-block h-4 w-4 text-yellow-600" />
                            )}
                          </div>
                          <div className="px-4 py-4 text-left">
                            <p className="text-xs text-muted-foreground">
                              {new Date(
                                classification.created_at
                              ).toLocaleDateString("fr-FR", {
                                day: "2-digit",
                                month: "short",
                                year: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </p>
                          </div>
                        </div>
                      </button>
                      {isExpanded && (
                        <ExpandedRow classification={classification} />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between rounded-xl border border-border bg-card px-4 py-3 shadow-sm">
        <p className="text-sm text-muted-foreground">
          Affichage de {startItem} à {endItem} sur {totalItems} résultat
          {totalItems !== 1 ? "s" : ""}
        </p>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="rounded-lg border border-input bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            Précédent
          </button>

          <div className="flex items-center gap-1">
            {[...Array(totalPages)].map((_, i) => {
              const page = i + 1;
              const showPage =
                page === 1 ||
                page === totalPages ||
                (page >= currentPage - 1 && page <= currentPage + 1);

              if (!showPage) {
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return (
                    <span
                      key={page}
                      className="px-2 text-sm text-muted-foreground"
                    >
                      ...
                    </span>
                  );
                }
                return null;
              }

              return (
                <button
                  key={page}
                  onClick={() => onPageChange(page)}
                  className={`h-8 w-8 rounded-lg text-sm font-medium transition-colors ${
                    page === currentPage
                      ? "bg-primary text-primary-foreground"
                      : "bg-background text-foreground hover:bg-accent"
                  }`}
                >
                  {page}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="rounded-lg border border-input bg-background px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
          >
            Suivant
          </button>
        </div>
      </div>
    </div>
  );
}

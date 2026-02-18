"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { FilterBar } from "@/components/database/FilterBar";
import { DataTable } from "@/components/database/DataTable";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import type { ClassificationListResponse } from "@/types/api";

export default function DatabasePage() {
  const { currentConfigId } = useConfigStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [minConfidence, setMinConfidence] = useState(0);
  const [maxConfidence, setMaxConfidence] = useState(100);
  const [challengedFilter, setChallengedFilter] = useState<boolean | null>(
    null
  );
  const [currentPage, setCurrentPage] = useState(1);

  const pageSize = 20;

  const queryParams = useMemo(() => {
    const params = new URLSearchParams({
      page: String(currentPage),
      page_size: String(pageSize),
      min_confidence: String(minConfidence / 100),
      max_confidence: String(maxConfidence / 100),
    });

    if (currentConfigId) {
      params.set("config_id", currentConfigId);
    }

    if (challengedFilter !== null) {
      params.set("was_challenged", String(challengedFilter));
    }

    if (searchQuery.trim()) {
      params.set("search", searchQuery.trim());
    }

    return params.toString();
  }, [
    currentConfigId,
    currentPage,
    pageSize,
    minConfidence,
    maxConfidence,
    challengedFilter,
    searchQuery,
  ]);

  const { data, isLoading } = useQuery({
    queryKey: ["classifications", queryParams],
    queryFn: () =>
      apiFetch<ClassificationListResponse>(
        `/api/classifications?${queryParams}`
      ),
    enabled: !!currentConfigId,
  });

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleFilterChange = () => {
    setCurrentPage(1);
  };

  return (
    <div className="h-screen overflow-y-auto bg-background p-6">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-foreground">
            Base de donnees
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Explorez et analysez toutes les classifications effectuees
          </p>
        </div>

        {!currentConfigId ? (
          <div className="rounded-xl border border-border bg-card p-8 text-center shadow-sm">
            <p className="text-sm text-muted-foreground">
              Selectionnez une configuration pour afficher les classifications
            </p>
          </div>
        ) : (
          <>
            <FilterBar
              searchQuery={searchQuery}
              onSearchChange={(value) => {
                setSearchQuery(value);
                handleFilterChange();
              }}
              minConfidence={minConfidence}
              onMinConfidenceChange={(value) => {
                setMinConfidence(value);
                handleFilterChange();
              }}
              maxConfidence={maxConfidence}
              onMaxConfidenceChange={(value) => {
                setMaxConfidence(value);
                handleFilterChange();
              }}
              challengedFilter={challengedFilter}
              onChallengedFilterChange={(value) => {
                setChallengedFilter(value);
                handleFilterChange();
              }}
              totalCount={data?.total ?? 0}
            />

            <DataTable
              data={data?.items ?? []}
              isLoading={isLoading}
              currentPage={currentPage}
              pageSize={pageSize}
              totalItems={data?.total ?? 0}
              onPageChange={handlePageChange}
            />
          </>
        )}
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  MessageSquare,
  Factory,
  Database,
  BarChart3,
  FlaskConical,
  ChevronDown,
  Plus,
  Trash2,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useConfigStore } from "@/hooks/useConfig";
import { useConversationStore } from "@/hooks/useConversation";
import type { ConfigResponse, ConversationResponse } from "@/types/api";

const NAV_SECTIONS = [
  {
    label: "Outils",
    items: [
      { href: "/backoffice", label: "Backoffice", icon: Factory },
      { href: "/database", label: "Database", icon: Database },
    ],
  },
  {
    label: "Analyse",
    items: [
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/evaluation", label: "Evaluation", icon: FlaskConical },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { currentConfigId, setConfigId } = useConfigStore();
  const { currentConversationId, setConversationId } = useConversationStore();

  const { data: configs } = useQuery({
    queryKey: ["configs"],
    queryFn: () => apiFetch<ConfigResponse[]>("/api/configs"),
  });

  const { data: conversations } = useQuery({
    queryKey: ["conversations", currentConfigId],
    queryFn: () =>
      apiFetch<{ items: ConversationResponse[] }>(
        `/api/conversations?config_id=${currentConfigId}`
      ).then((r) => r.items),
    enabled: !!currentConfigId,
  });

  useEffect(() => {
    if (!currentConfigId && configs && configs.length > 0) {
      setConfigId(configs[0].id);
    }
  }, [configs, currentConfigId, setConfigId]);

  const currentConfig = configs?.find((c) => c.id === currentConfigId);
  const recentConversations = (conversations ?? []).slice(0, 5);

  const handleConfigChange = (newConfigId: string) => {
    setConfigId(newConfigId);
    setConversationId(null);
  };

  const queryClient = useQueryClient();

  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    try {
      await apiFetch(`/api/conversations/${convId}`, { method: "DELETE" });
    } catch {
      // Conversation already gone — proceed with cleanup
    }
    if (currentConversationId === convId) {
      setConversationId(null);
    }
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };

  const handleNewConversation = () => {
    setConversationId(null);
    if (pathname !== "/") router.push("/");
  };

  const handleSelectConversation = (convId: string) => {
    setConversationId(convId);
    if (pathname !== "/") router.push("/");
  };

  return (
    <aside className="group fixed left-0 top-3 bottom-3 z-50 flex w-[68px] flex-col rounded-r-2xl bg-[var(--sidebar)] shadow-[4px_0_24px_rgba(151,103,255,0.08)] transition-all duration-300 ease-in-out hover:w-[240px]">
      <div className="flex h-16 items-center gap-3 overflow-hidden px-3.5">
        <Image
          src="/logo.jpeg"
          alt="AlloClass"
          width={40}
          height={40}
          className="h-10 w-10 shrink-0 rounded-xl"
        />
        <span className="whitespace-nowrap text-sm font-semibold text-[var(--sidebar-foreground)] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          AlloClass
        </span>
      </div>

      <nav className="mt-2 flex flex-1 flex-col gap-5 px-3">
        <div className="flex flex-col gap-1">
          <div className="mb-1 flex items-center gap-2 px-2">
            <span className="h-px w-4 shrink-0 bg-[var(--sidebar-foreground)] opacity-10 group-hover:hidden" />
            <span className="hidden truncate text-[10px] font-semibold uppercase tracking-widest text-[var(--sidebar-foreground)] opacity-40 group-hover:block">
              Chat
            </span>
          </div>

          <button
            onClick={handleNewConversation}
            className={`relative flex h-11 items-center gap-3 rounded-lg px-3 transition-colors ${
              pathname === "/" && !currentConversationId
                ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
                : "text-[var(--sidebar-foreground)] opacity-50 hover:opacity-100 hover:bg-[var(--sidebar-accent)]"
            }`}
          >
            {pathname === "/" && !currentConversationId && (
              <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-[var(--sidebar-primary)]" />
            )}
            <Plus className="h-[22px] w-[22px] shrink-0" />
            <span className="whitespace-nowrap text-sm font-medium opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              Nouveau chat
            </span>
          </button>

          {recentConversations.map((conv) => {
            const isActive = currentConversationId === conv.id && pathname === "/";
            return (
              <div
                key={conv.id}
                onClick={() => handleSelectConversation(conv.id)}
                className={`group/conv relative flex w-full h-7 cursor-pointer items-center gap-2.5 rounded-md pl-5 pr-1 transition-colors ${
                  isActive
                    ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
                    : "text-[var(--sidebar-foreground)] opacity-30 hover:opacity-70 hover:bg-[var(--sidebar-accent)]"
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-3 w-[2px] -translate-y-1/2 rounded-r-full bg-[var(--sidebar-primary)]" />
                )}
                <MessageSquare className="h-3 w-3 shrink-0" />
                <span className="min-w-0 flex-1 truncate whitespace-nowrap text-[11px] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  {conv.title ?? "Sans titre"}
                </span>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  className="shrink-0 rounded p-0.5 text-red-400 opacity-0 transition-opacity hover:text-red-300 hover:bg-red-500/10 group-hover:group-hover/conv:opacity-100"
                >
                  <Trash2 className="h-2.5 w-2.5" />
                </button>
              </div>
            );
          })}
        </div>

        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className="flex flex-col gap-1">
            <div className="mb-1 flex items-center gap-2 px-2">
              <span className="h-px w-4 shrink-0 bg-[var(--sidebar-foreground)] opacity-10 group-hover:hidden" />
              <span className="hidden truncate text-[10px] font-semibold uppercase tracking-widest text-[var(--sidebar-foreground)] opacity-40 group-hover:block">
                {section.label}
              </span>
            </div>

            {section.items.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`relative flex h-11 items-center gap-3 rounded-lg px-3 transition-colors ${
                    isActive
                      ? "bg-[var(--sidebar-accent)] text-[var(--sidebar-primary)]"
                      : "text-[var(--sidebar-foreground)] opacity-50 hover:opacity-100 hover:bg-[var(--sidebar-accent)]"
                  }`}
                >
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-[var(--sidebar-primary)]" />
                  )}
                  <Icon className="h-[22px] w-[22px] shrink-0" />
                  <span className="whitespace-nowrap text-sm font-medium opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                    {label}
                  </span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="px-3 pb-4">
        <div className="relative">
          <select
            value={currentConfigId ?? ""}
            onChange={(e) => handleConfigChange(e.target.value)}
            className="w-full appearance-none truncate rounded-lg bg-[var(--sidebar-accent)] py-2 pl-3 pr-7 text-xs font-medium text-[var(--sidebar-foreground)] opacity-0 transition-opacity duration-300 focus:outline-none group-hover:opacity-100"
          >
            {!configs && <option value="">Chargement...</option>}
            {configs?.length === 0 && <option value="">Aucune config</option>}
            {configs?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-[var(--sidebar-foreground)] opacity-0 transition-opacity duration-300 group-hover:opacity-50" />

          <div className="absolute inset-0 flex items-center justify-center group-hover:hidden">
            <div
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: currentConfig ? "var(--sidebar-primary)" : "var(--sidebar-foreground)" }}
            />
          </div>
        </div>
      </div>
    </aside>
  );
}

"use client";

import { useRef, useState } from "react";
import {
  ArrowUp,
  Square,
  Plus,
  Scan,
  Search,
  MessageSquareWarning,
  ListChecks,
  BarChart3,
  Lightbulb,
  Settings2,
  Layers,
  BookOpen,
  History,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  PromptInput,
  PromptInputAction,
  PromptInputActions,
  PromptInputTextarea,
} from "@/components/prompt-kit/prompt-input";
import { Button } from "@/components/ui/button";

const TOOL_HINTS = [
  { icon: Scan, label: "Classifier un ticket", prompt: "Classifie ce ticket : " },
  { icon: Layers, label: "Classification par lot", prompt: "Classifie ces tickets :\n1. " },
  { icon: Search, label: "Rechercher des tickets", prompt: "Recherche les tickets " },
  { icon: MessageSquareWarning, label: "Corriger une classification", prompt: "Corrige : " },
  { icon: ListChecks, label: "File de revision", prompt: "Montre-moi les prochains tickets a revoir" },
  { icon: BarChart3, label: "Indicateurs de performance", prompt: "Donne-moi les indicateurs de performance" },
  { icon: Lightbulb, label: "Pistes d'amelioration", prompt: "Quelles sont les pistes d'amelioration ?" },
  { icon: Settings2, label: "Configuration active", prompt: "Decris-moi la configuration active" },
  { icon: BookOpen, label: "Regles apprises", prompt: "Quelles regles le systeme a-t-il apprises ?" },
  { icon: History, label: "Historique des versions", prompt: "Montre-moi l'historique des versions du systeme" },
];

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled: boolean;
}

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  disabled,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  };

  const handleToolSelect = (prompt: string) => {
    setValue(prompt);
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  return (
    <div className="bg-background px-4 py-3">
      <div className="mx-auto max-w-3xl">
        <PromptInput
          value={value}
          onValueChange={setValue}
          isLoading={isStreaming}
          onSubmit={handleSubmit}
          disabled={disabled}
          className="border-border bg-card shadow-sm"
        >
          <PromptInputTextarea
            ref={textareaRef}
            placeholder="Collez un ticket ou posez une question..."
          />

          <PromptInputActions className="flex items-center justify-between px-2 pb-1">
            <PromptInputAction tooltip="Actions">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <div className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full transition-colors hover:bg-muted">
                    <Plus className="size-4 text-muted-foreground" />
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  side="top"
                  align="start"
                  className="max-h-64 overflow-y-auto"
                >
                  {TOOL_HINTS.map(({ icon: Icon, label, prompt }) => (
                    <DropdownMenuItem
                      key={label}
                      onClick={() => handleToolSelect(prompt)}
                      className="gap-2.5"
                    >
                      <Icon className="size-4 shrink-0 text-primary" />
                      <span className="text-sm">{label}</span>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </PromptInputAction>

            <PromptInputAction
              tooltip={isStreaming ? "Arreter" : "Envoyer"}
            >
              <Button
                variant="default"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={isStreaming ? onStop : handleSubmit}
                disabled={!isStreaming && !value.trim()}
              >
                {isStreaming ? (
                  <Square className="size-4 fill-current" />
                ) : (
                  <ArrowUp className="size-4" />
                )}
              </Button>
            </PromptInputAction>
          </PromptInputActions>
        </PromptInput>
      </div>
    </div>
  );
}

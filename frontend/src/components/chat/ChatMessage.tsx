"use client";

import {
  User,
  Loader2,
  Search,
  Shield,
  BarChart3,
  MessageSquareWarning,
  ListChecks,
  FlaskConical,
  Lightbulb,
  Settings,
  BookOpen,
  History,
  Layers,
} from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtItem,
  ChainOfThoughtStep,
  ChainOfThoughtTrigger,
} from "@/components/prompt-kit/chain-of-thought";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ClassificationCard } from "./ClassificationCard";
import { LearningCard } from "./LearningCard";
import type { AgentStep, ChatMessage as ChatMessageType } from "@/hooks/useChat";

interface ChatMessageProps {
  message: ChatMessageType;
}

const TOOL_ICONS: Record<string, React.ReactNode> = {
  classify_ticket: <Shield className="size-4" />,
  classify_batch: <Layers className="size-4" />,
  search_tickets: <Search className="size-4" />,
  correct_classification: <MessageSquareWarning className="size-4" />,
  get_review_queue: <ListChecks className="size-4" />,
  get_stats: <BarChart3 className="size-4" />,
  run_evaluation: <FlaskConical className="size-4" />,
  get_improvement_suggestions: <Lightbulb className="size-4" />,
  get_config_info: <Settings className="size-4" />,
  get_learned_rules: <BookOpen className="size-4" />,
  get_version_history: <History className="size-4" />,
};

function AgentSteps({ steps }: { steps: AgentStep[] }) {
  if (steps.length === 0) return null;

  return (
    <ChainOfThought>
      {steps.map((step, i) => (
        <ChainOfThoughtStep key={i}>
          <ChainOfThoughtTrigger
            leftIcon={
              step.status === "running" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                TOOL_ICONS[step.tool] ?? <Shield className="size-4" />
              )
            }
            swapIconOnHover={step.status !== "running"}
          >
            <span className={step.status === "error" ? "text-destructive" : ""}>
              {step.status === "done" || step.status === "error"
                ? step.summary ?? step.label
                : step.label}
            </span>
          </ChainOfThoughtTrigger>
          {step.summary && step.status !== "running" && (
            <ChainOfThoughtContent>
              <ChainOfThoughtItem>{step.label}</ChainOfThoughtItem>
              <ChainOfThoughtItem className="font-medium text-foreground">
                {step.summary}
              </ChainOfThoughtItem>
            </ChainOfThoughtContent>
          )}
        </ChainOfThoughtStep>
      ))}
    </ChainOfThought>
  );
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isBot = message.role === "assistant";
  const isLoading = isBot && !message.content && message.steps.length === 0;
  const hasClassification = message.data?.type === "classification" || message.data?.results;

  return (
    <div className={`flex gap-3 ${isBot ? "" : "flex-row-reverse"}`}>
      {isBot ? (
        <img
          src="/logo.jpeg"
          alt="AlloClass"
          className="h-8 w-8 shrink-0 rounded-full object-cover"
        />
      ) : (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <User className="h-4 w-4" />
        </div>
      )}

      <div className={`flex max-w-[75%] flex-col gap-2 ${isBot ? "" : "items-end"}`}>
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Reflexion en cours...</span>
          </div>
        )}

        <AgentSteps steps={message.steps} />

        {message.content && (
          <div
            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
              isBot
                ? "bg-card text-card-foreground shadow-sm border border-border"
                : "bg-primary text-primary-foreground"
            }`}
          >
            {isBot ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  ul: ({ children }) => <ul className="mb-2 ml-4 list-disc last:mb-0">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal last:mb-0">{children}</ol>,
                  li: ({ children }) => <li className="mb-0.5">{children}</li>,
                  h1: ({ children }) => <h1 className="mb-2 text-base font-bold">{children}</h1>,
                  h2: ({ children }) => <h2 className="mb-1.5 text-sm font-bold">{children}</h2>,
                  h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{children}</h3>,
                  code: ({ children, className }) => {
                    const isBlock = className?.includes("language-");
                    if (isBlock) {
                      return (
                        <pre className="my-2 overflow-x-auto rounded-lg bg-muted p-3 text-xs">
                          <code>{children}</code>
                        </pre>
                      );
                    }
                    return (
                      <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">{children}</code>
                    );
                  },
                  blockquote: ({ children }) => (
                    <blockquote className="my-2 border-l-2 border-primary/30 pl-3 italic text-muted-foreground">
                      {children}
                    </blockquote>
                  ),
                  hr: () => <hr className="my-3 border-border" />,
                  table: ({ children }) => (
                    <div className="my-2 overflow-x-auto">
                      <table className="w-full text-xs">{children}</table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-border bg-muted px-2 py-1 text-left font-semibold">{children}</th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-border px-2 py-1">{children}</td>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            ) : (
              message.content
            )}
          </div>
        )}

        {hasClassification && message.data ? (
          <ClassificationCard data={message.data as Record<string, unknown>} />
        ) : null}

        {message.learningCard ? (
          <LearningCard card={message.learningCard} />
        ) : null}
      </div>
    </div>
  );
}

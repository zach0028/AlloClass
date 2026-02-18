"use client";

import Image from "next/image";
import { BarChart3, Lightbulb, ClipboardCheck } from "lucide-react";

interface WelcomeScreenProps {
  hasConfig: boolean;
  onQuickAction: (text: string) => void;
}

const QUICK_ACTIONS = [
  {
    icon: BarChart3,
    label: "Indicateurs de performance",
    message: "Donne-moi une vue d'ensemble des performances de classification",
  },
  {
    icon: Lightbulb,
    label: "Pistes d'amelioration",
    message: "Quelles sont les pistes d'amelioration du systeme ?",
  },
  {
    icon: ClipboardCheck,
    label: "Reviser un ticket",
    message: "Montre-moi le prochain ticket a reviser",
  },
];

export function WelcomeScreen({ hasConfig, onQuickAction }: WelcomeScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4">
      <div className="flex flex-col items-center gap-4 text-center">
        <Image
          src="/logo.jpeg"
          alt="AlloClass"
          width={72}
          height={72}
          className="h-[72px] w-[72px] rounded-2xl shadow-md"
        />
        <div>
          <h1 className="text-xl font-semibold text-foreground">
            Bienvenue sur AlloClass
          </h1>
          <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">
            Classification intelligente de tickets par LLM
          </p>
        </div>
      </div>

      {hasConfig ? (
        <div className="flex flex-wrap justify-center gap-3">
          {QUICK_ACTIONS.map(({ icon: Icon, label, message }) => (
            <button
              key={label}
              onClick={() => onQuickAction(message)}
              className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium shadow-sm transition-colors hover:bg-accent"
            >
              <Icon className="h-4 w-4 text-primary" />
              {label}
            </button>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">
          Chargement de la configuration...
        </p>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { WelcomeScreen } from "./WelcomeScreen";

export function ChatContainer() {
  const { messages, isStreaming, sendMessage, stopStreaming, configId } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className={`flex-1 overflow-y-auto ${hasMessages ? "" : "flex flex-col"}`}>
        {hasMessages ? (
          <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
          </div>
        ) : (
          <WelcomeScreen
            hasConfig={!!configId}
            onQuickAction={sendMessage}
          />
        )}
      </div>

      <ChatInput
        onSend={sendMessage}
        onStop={stopStreaming}
        isStreaming={isStreaming}
        disabled={!configId}
      />
    </div>
  );
}

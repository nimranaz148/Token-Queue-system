"use client";

import * as React from "react";
import { MessageSquare, Send, X, Bot, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ChatMessageItem {
  id?: string;
  role: "patient" | "assistant";
  content: string;
  at?: string;
}

export interface PatientChatWidgetProps {
  publicCode: string;
}

export function PatientChatWidget({ publicCode }: PatientChatWidgetProps): React.ReactElement {
  const [isOpen, setIsOpen] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessageItem[]>([]);
  const [inputValue, setInputValue] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [isFetchingHistory, setIsFetchingHistory] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadHistory = React.useCallback(async () => {
    if (!publicCode) return;
    setIsFetchingHistory(true);
    try {
      const res = await fetch(`/api/v1/public/tokens/${publicCode}/chat`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch {
      // Non-blocking history load
    } finally {
      setIsFetchingHistory(false);
    }
  }, [publicCode]);

  React.useEffect(() => {
    if (isOpen) {
      void loadHistory();
    }
  }, [isOpen, loadHistory]);

  React.useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setError(null);
    const newPatientMsg: ChatMessageItem = {
      role: "patient",
      content: text,
      at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, newPatientMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const res = await fetch(`/api/v1/public/tokens/${publicCode}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Jawab lanay mein masla pesh aya.");
      }

      const data = await res.json();
      const assistantMsg: ChatMessageItem = {
        role: "assistant",
        content: data.reply,
        at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    "Mera number kab aayega?",
    "Aagay kitnay mareez hain?",
    "Clinic ke auqat (timings)?",
  ];

  return (
    <div className="w-full">
      {!isOpen ? (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="w-full py-3 px-4 bg-surface-raised border border-accent/40 rounded-xl flex items-center justify-between text-left hover:border-accent transition-colors shadow-sm"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-accent/10 flex items-center justify-center text-accent flex-shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-fg">Queue Assistant (F-019)</p>
              <p className="text-[11px] text-fg-muted">Apnay token ya waqt ke baray mein poochein</p>
            </div>
          </div>
          <span className="text-xs text-accent font-medium px-2 py-1 bg-accent/10 rounded">
            Chat Shuru Karein
          </span>
        </button>
      ) : (
        <div className="bg-surface-raised border border-border rounded-xl shadow-lg flex flex-col overflow-hidden transition-all h-[420px]">
          {/* Header */}
          <div className="p-3 bg-surface border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center text-accent">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-fg">Queue Assistant</h3>
                <p className="text-[10px] text-fg-muted">Sirf queue & clinic maloomat</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-md text-fg-muted hover:text-fg hover:bg-surface-sunken"
              aria-label="Close chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Medical refusal notice */}
          <div className="bg-amber-500/10 px-3 py-1.5 border-b border-amber-500/20 text-[10px] text-amber-500 font-medium text-center">
            Yeh AI assistant sirf queue ki maloomat deta hai, tibbi mashwara nahi.
          </div>

          {/* Messages container */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
            {isFetchingHistory ? (
              <div className="flex items-center justify-center h-full text-fg-muted gap-2">
                <RefreshCw className="w-4 h-4 animate-spin text-accent" />
                <span>Pehle ki chat load ho rahi hai...</span>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-fg-muted space-y-2 p-4">
                <Bot className="w-8 h-8 text-fg-muted/40" />
                <p className="text-xs font-medium text-fg">Khush Amdeed!</p>
                <p className="text-[11px] max-w-xs">
                  Aap apnay token number, andaazan intezar, ya clinic ke baray mein sawal pooch saktay hain.
                </p>
              </div>
            ) : (
              messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex ${m.role === "patient" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[82%] px-3 py-2 rounded-xl text-xs leading-relaxed ${
                      m.role === "patient"
                        ? "bg-accent text-accent-fg rounded-br-none"
                        : "bg-surface border border-border text-fg rounded-bl-none shadow-sm"
                    }`}
                  >
                    {m.content}
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-surface border border-border px-3 py-2 rounded-xl rounded-bl-none text-xs text-fg-muted flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse delay-75" />
                  <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse delay-150" />
                  <span className="ml-1 text-[11px]">Assistant soch raha hai...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          {messages.length < 2 && !isLoading && (
            <div className="px-3 py-1.5 flex gap-1.5 overflow-x-auto bg-surface/50 border-t border-border">
              {quickPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSendMessage(prompt)}
                  className="text-[10px] px-2 py-1 rounded bg-surface border border-border text-fg-muted hover:text-fg whitespace-nowrap hover:border-accent transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="px-3 py-1.5 bg-red-500/10 text-red-500 text-[11px] flex items-center gap-1.5 border-t border-red-500/20">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">{error}</span>
            </div>
          )}

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="p-2.5 bg-surface border-t border-border flex items-center gap-2"
          >
            <input
              type="text"
              aria-label="Sawal likhein"
              placeholder="Sawal likhein (1-300 chars)..."
              maxLength={300}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isLoading}
              className="flex-1 h-9 px-3 bg-surface-raised border border-border rounded-lg text-xs text-fg placeholder:text-fg-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <Button
              type="submit"
              variant="primary"
              disabled={!inputValue.trim() || isLoading}
              className="h-9 w-9 p-0 flex items-center justify-center flex-shrink-0"
              aria-label="Bheinjein"
            >
              <Send className="w-3.5 h-3.5" />
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}

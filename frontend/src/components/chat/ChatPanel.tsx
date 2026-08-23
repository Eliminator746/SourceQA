import { useEffect, useRef } from "react";

import type { ChatMessage } from "../../types/chat";

import AnswerCard from "./AnswerCard";

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading?: boolean;
}

export default function ChatPanel({ messages, isLoading = false }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <section
        className="flex-1 flex items-center justify-center text-center px-6"
        aria-label="Conversation"
      >
        <div>
          <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">💬</span>
          </div>
          <h2 className="text-lg font-semibold text-gray-700 mb-1">
            Ask a question
          </h2>
          <p className="text-sm text-gray-400">
            Upload your documents and ask questions about their content.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section
      className="flex-1 overflow-y-auto px-6 py-4 space-y-6"
      aria-label="Conversation"
    >
      {messages.map((message) => {
        if (message.role === "user") {
          return (
            <div key={message.id} className="flex justify-end">
              <div className="max-w-[75%] bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
                <p className="text-sm leading-relaxed">{message.content}</p>
              </div>
            </div>
          );
        }

        return (
          <div key={message.id} className="flex flex-col gap-2 max-w-[85%]">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center shrink-0">
                <span className="text-white text-xs font-bold">R</span>
              </div>
              <span className="text-xs font-medium text-gray-500">
                Assistant
              </span>
            </div>
            <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100">
              <AnswerCard answer={message.content} sources={message.sources} />
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex flex-col gap-2 max-w-[85%]">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-bold">R</span>
            </div>
            <span className="text-xs font-medium text-gray-500">
              Assistant
            </span>
          </div>
          <div
            role="status"
            aria-live="polite"
            className="inline-flex w-fit items-center gap-2 bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100 text-sm text-gray-500"
          >
            <svg
              className="animate-spin w-4 h-4 text-indigo-500"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Searching your documents…
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </section>
  );
}

import { useEffect, useRef } from "react";

import type { ChatMessage } from "../../types/chat";

import AnswerCard from "./AnswerCard";
import CitationList from "./CitationList";

interface ChatPanelProps {
  messages: ChatMessage[];
}

export default function ChatPanel({ messages }: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <section className="chat-panel" aria-label="Conversation">
        <div>
          <h2>Ask a question</h2>

          <p>Upload your documents and ask questions about their content.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="chat-panel" aria-label="Conversation">
      {messages.map((message) => {
        if (message.role === "user") {
          return (
            <div key={message.id} className="chat-message user-message">
              <div>
                <span>You</span>

                <p>{message.content}</p>
              </div>
            </div>
          );
        }

        return (
          <div key={message.id} className="chat-message assistant-message">
            <span>Assistant</span>

            <AnswerCard answer={message.content} />

            {message.sources && message.sources.length > 0 && (
              <CitationList sources={message.sources} />
            )}
          </div>
        );
      })}

      <div ref={bottomRef} />
    </section>
  );
}

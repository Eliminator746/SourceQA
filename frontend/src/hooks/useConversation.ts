import { useCallback, useState } from "react";

import type { QueryResponse } from "../types/query";
import type { ChatMessage } from "../types/chat";

function createMessageId(): string {
  return crypto.randomUUID();
}

export function useConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const addUserMessage = useCallback((content: string) => {
    const message: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content,
    };

    setMessages((previous) => [...previous, message]);
  }, []);

  const addAssistantMessage = useCallback((response: QueryResponse) => {
    const message: ChatMessage = {
      id: createMessageId(),
      role: "assistant",
      content: response.answer,
      sources: response.sources,
    };

    setMessages((previous) => [...previous, message]);
  }, []);

  const clearConversation = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    addUserMessage,
    addAssistantMessage,
    clearConversation,
  };
}

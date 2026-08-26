import { useCallback, useState } from "react";

import type { ChatMessage } from "../types/chat";

import type { QueryResponse, Source } from "../types/query";

function createMessageId(): string {
  return crypto.randomUUID();
}

export function useConversation() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>(
    undefined,
  );

  // ==========================================================
  // User message
  // ==========================================================

  const addUserMessage = useCallback((content: string) => {
    const message: ChatMessage = {
      id: createMessageId(),
      role: "user",
      content,
    };

    setMessages((previous) => [...previous, message]);
  }, []);

  // ==========================================================
  // Conversation ID
  // ==========================================================

  const updateConversationId = useCallback((id: string) => {
    setConversationId(id);
  }, []);

  // ==========================================================
  // Assistant message
  // ==========================================================

  const startAssistantMessage = useCallback((): string => {
    const id = createMessageId();

    const message: ChatMessage = {
      id,
      role: "assistant",
      content: "",
      sources: [],
      status: "searching",
    };

    setMessages((previous) => [...previous, message]);

    return id;
  }, []);

  // ==========================================================
  // Generic assistant update
  // ==========================================================

  const updateAssistantMessage = useCallback(
    (
      id: string,
      patch: Partial<Pick<ChatMessage, "content" | "sources" | "status">>,
    ) => {
      setMessages((previous) =>
        previous.map((message) =>
          message.id === id && message.role === "assistant"
            ? {
                ...message,
                ...patch,
              }
            : message,
        ),
      );
    },
    [],
  );

  // ==========================================================
  // Append streamed token
  // ==========================================================

  const appendAssistantToken = useCallback((id: string, text: string) => {
    setMessages((previous) =>
      previous.map((message) =>
        message.id === id && message.role === "assistant"
          ? {
              ...message,
              content: message.content + text,
              status: "generating",
            }
          : message,
      ),
    );
  }, []);

  // ==========================================================
  // Update sources
  // ==========================================================

  const updateAssistantSources = useCallback(
    (id: string, sources: Source[]) => {
      setMessages((previous) =>
        previous.map((message) =>
          message.id === id && message.role === "assistant"
            ? {
                ...message,
                sources,
              }
            : message,
        ),
      );
    },
    [],
  );

  // ==========================================================
  // Complete assistant message
  // ==========================================================

  const completeAssistantMessage = useCallback(
    (id: string, response: QueryResponse) => {
      setConversationId(response.conversation_id);

      setMessages((previous) =>
        previous.map((message) =>
          message.id === id && message.role === "assistant"
            ? {
                ...message,
                content: response.answer,
                sources: response.sources,
                status: "complete",
              }
            : message,
        ),
      );
    },
    [],
  );

  // ==========================================================
  // Remove message
  // ==========================================================

  const removeMessage = useCallback((id: string) => {
    setMessages((previous) => previous.filter((message) => message.id !== id));
  }, []);

  // ==========================================================
  // New Chat
  // ==========================================================

  const clearConversation = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
  }, []);

  return {
    messages,
    conversationId,

    addUserMessage,

    updateConversationId,

    startAssistantMessage,
    updateAssistantMessage,
    appendAssistantToken,
    updateAssistantSources,
    completeAssistantMessage,

    removeMessage,
    clearConversation,
  };
}

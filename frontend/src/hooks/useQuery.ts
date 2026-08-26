import { useState } from "react";

import {
  streamQuestion,
  type StreamHandlers,
  type StreamStatus,
} from "../api/query";

import type { QueryResponse } from "../types/query";

import { getApiErrorMessage } from "../utils/apiError";

export function useQuery() {
  const [isLoading, setIsLoading] = useState(false);

  const [streamStatus, setStreamStatus] = useState<StreamStatus | null>(null);

  const [error, setError] = useState<string | null>(null);

  // ==========================================================
  // Ask question
  // ==========================================================

  const ask = async (
    question: string,
    conversationId?: string,
    handlers: StreamHandlers = {},
  ): Promise<QueryResponse | null> => {
    setIsLoading(true);
    setStreamStatus("searching");
    setError(null);

    const wrappedHandlers: StreamHandlers = {
      // ------------------------------------------------------
      // Conversation ID
      // ------------------------------------------------------

      onConversationId: (id) => {
        handlers.onConversationId?.(id);
      },

      // ------------------------------------------------------
      // Status
      // ------------------------------------------------------

      onStatus: (status) => {
        setStreamStatus(status);

        handlers.onStatus?.(status);
      },

      // ------------------------------------------------------
      // Token
      // ------------------------------------------------------

      onToken: (text) => {
        handlers.onToken?.(text);
      },

      // ------------------------------------------------------
      // Sources
      // ------------------------------------------------------

      onSources: (sources) => {
        handlers.onSources?.(sources);
      },
    };

    try {
      const response = await streamQuestion(
        {
          question,
          conversation_id: conversationId,
        },
        wrappedHandlers,
      );

      return response;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : getApiErrorMessage(error);

      setError(message);

      return null;
    } finally {
      setIsLoading(false);
      setStreamStatus(null);
    }
  };

  // ==========================================================
  // Clear error
  // ==========================================================

  const clearError = () => {
    setError(null);
  };

  return {
    ask,
    isLoading,
    streamStatus,
    error,
    clearError,
  };
}

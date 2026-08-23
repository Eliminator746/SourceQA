import { useState } from "react";

import { askQuestion } from "../api/query";
import type { QueryResponse } from "../types/query";
import { getApiErrorMessage } from "../utils/apiError";

export function useQuery() {
  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const ask = async (
    question: string,
    conversationId?: string,
  ): Promise<QueryResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await askQuestion({
        question,
        conversation_id: conversationId,
      });

      return response;
    } catch (error) {
      const message = getApiErrorMessage(error);

      setError(message);

      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const clearError = () => {
    setError(null);
  };

  return {
    ask,
    isLoading,
    error,
    clearError,
  };
}

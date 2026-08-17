import { useState } from "react";

import { askQuestion } from "../api/query";

import type { QueryRequest, QueryResponse } from "../types/query";

interface UseQueryResult {
  response: QueryResponse | null;

  isLoading: boolean;

  error: string | null;

  ask: (question: string) => Promise<QueryResponse | null>;

  clear: () => void;
}

export function useQuery(): UseQueryResult {
  const [response, setResponse] = useState<QueryResponse | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // --------------------------------------------------
  // Ask question
  // --------------------------------------------------

  const ask = async (question: string): Promise<QueryResponse | null> => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setError("Question cannot be empty.");

      return null;
    }

    try {
      setIsLoading(true);

      setError(null);

      const request: QueryRequest = {
        question: trimmedQuestion,
      };

      const result = await askQuestion(request);

      setResponse(result);

      return result;
    } catch (error) {
      console.error("Failed to process question:", error);

      setResponse(null);

      setError("Unable to get an answer. Please try again.");

      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // --------------------------------------------------
  // Clear current answer
  // --------------------------------------------------

  const clear = () => {
    setResponse(null);

    setError(null);
  };

  return {
    response,
    isLoading,
    error,
    ask,
    clear,
  };
}

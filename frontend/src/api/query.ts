import apiClient from "./client";

import type { QueryRequest, QueryResponse } from "../types/query";

export const askQuestion = async (
  data: QueryRequest,
): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>("/api/query", data);

  return response.data;
};

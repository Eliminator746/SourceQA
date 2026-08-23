export interface QueryRequest {
  question: string;
  conversation_id?: string;
}

export interface Source {
  document_id: string;
  filename: string;
  page?: number;
  chunk_index?: number;
}

export interface QueryResponse {
  conversation_id: string;
  answer: string;
  sources: Source[];
}

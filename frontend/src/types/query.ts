export interface QueryRequest {
  question: string;
}

export interface Source {
  document_id: string;
  filename: string;
  page: number | null;
  chunk_index: number | null;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

export interface QueryRequest {
  question: string;
}

export interface Source {
  document_id: string;
  filename: string;
  page?: number;
  page_label?: string;
  chunk_index?: number;
  content?: string;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

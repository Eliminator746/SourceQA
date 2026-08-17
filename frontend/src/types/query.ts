export interface QueryRequest {
  question: string;
}

export interface Source {
  filename: string;
  page?: number;
  page_label?: string;
  chunk_index?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
}

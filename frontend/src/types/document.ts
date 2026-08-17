export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  created_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  count: number;
  max_sources: number;
}

export interface DocumentUploadResponse {
  message: string;
  document_id: string;
  filename: string;
  status: string;
}

export interface DocumentDeleteResponse {
  message: string;
}

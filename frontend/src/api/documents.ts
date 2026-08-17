import apiClient from "./client";

import type {
  DocumentListResponse,
  DocumentUploadResponse,
  DocumentDeleteResponse,
} from "../types/document";

export const getDocuments = async (): Promise<DocumentListResponse> => {
  const response = await apiClient.get<DocumentListResponse>("/api/documents");

  return response.data;
};

export const uploadDocument = async (
  file: File,
): Promise<DocumentUploadResponse> => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await apiClient.post<DocumentUploadResponse>(
    "/api/documents/upload",
    formData,
  );

  return response.data;
};

export const deleteDocument = async (
  documentId: string,
): Promise<DocumentDeleteResponse> => {
  const response = await apiClient.delete<DocumentDeleteResponse>(
    `/api/documents/${documentId}`,
  );

  return response.data;
};

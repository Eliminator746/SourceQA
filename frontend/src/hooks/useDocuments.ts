import { useCallback, useEffect, useState } from "react";

import { getDocuments, uploadDocument, deleteDocument } from "../api/documents";

import type { Document } from "../types/document";

interface UseDocumentsResult {
  documents: Document[];
  count: number;
  maxSources: number;

  isLoading: boolean;
  isUploading: boolean;
  error: string | null;

  refreshDocuments: () => Promise<void>;
  upload: (file: File) => Promise<void>;
  remove: (documentId: string) => Promise<void>;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<Document[]>([]);

  const [count, setCount] = useState(0);

  const [maxSources, setMaxSources] = useState(5);

  const [isLoading, setIsLoading] = useState(true);

  const [isUploading, setIsUploading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // --------------------------------------------------
  // Fetch documents
  // --------------------------------------------------

  const refreshDocuments = useCallback(async () => {
    try {
      setError(null);

      const response = await getDocuments();

      setDocuments(response.documents);

      setCount(response.count);

      setMaxSources(response.max_sources);
    } catch (error) {
      console.error("Failed to fetch documents:", error);

      setError("Unable to load your documents.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // --------------------------------------------------
  // Initial document load
  // --------------------------------------------------

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  // --------------------------------------------------
  // Poll while any document is still being indexed
  // --------------------------------------------------

  useEffect(() => {
    const hasProcessing = documents.some((doc) => doc.status === "processing");
    if (!hasProcessing) return;

    const interval = setInterval(refreshDocuments, 3000);
    return () => clearInterval(interval);
  }, [documents, refreshDocuments]);

  // --------------------------------------------------
  // Upload document
  // --------------------------------------------------

  const upload = async (file: File): Promise<void> => {
    try {
      setError(null);

      setIsUploading(true);

      await uploadDocument(file);

      // Refresh the document list after successful
      // upload and ingestion.
      await refreshDocuments();
    } catch (error) {
      console.error("Failed to upload document:", error);

      setError("Unable to upload the document.");

      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  // --------------------------------------------------
  // Delete document
  // --------------------------------------------------

  const remove = async (documentId: string): Promise<void> => {
    try {
      setError(null);

      await deleteDocument(documentId);

      // Remove it from the UI immediately.
      setDocuments((currentDocuments) =>
        currentDocuments.filter((document) => document.id !== documentId),
      );

      setCount((currentCount) => Math.max(0, currentCount - 1));
    } catch (error) {
      console.error("Failed to delete document:", error);

      setError("Unable to delete the document.");

      throw error;
    }
  };

  return {
    documents,
    count,
    maxSources,

    isLoading,
    isUploading,
    error,

    refreshDocuments,
    upload,
    remove,
  };
}

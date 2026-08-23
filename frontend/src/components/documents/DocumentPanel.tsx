import UploadDocument from "./UploadDocument";
import DocumentItem from "./DocumentItem";

import type { Document } from "../../types/document";

interface DocumentPanelProps {
  documents: Document[];
  count: number;
  maxSources: number;

  isLoading: boolean;
  isUploading: boolean;

  error: string | null;

  onUpload: (file: File) => Promise<void>;
  onDelete: (documentId: string) => Promise<void>;
}

export default function DocumentPanel({
  documents,
  count,
  maxSources,
  isLoading,
  isUploading,
  error,
  onUpload,
  onDelete,
}: DocumentPanelProps) {
  const uploadLimitReached = count >= maxSources;

  return (
    <aside className="w-72 bg-white border-l border-gray-200 flex flex-col overflow-hidden shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 shrink-0">
        <h2 className="text-sm font-semibold text-gray-900">Your Sources</h2>
        <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5 font-medium">
          {count} / {maxSources}
        </span>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto p-3">
        {isLoading && (
          <p className="text-sm text-gray-400 text-center py-8">
            Loading documents...
          </p>
        )}

        {!isLoading && documents.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <span className="text-3xl mb-3">📂</span>
            <p className="text-sm text-gray-400">No documents uploaded yet.</p>
          </div>
        )}

        {!isLoading && documents.length > 0 && (
          <div className="space-y-1">
            {documents.map((document) => (
              <DocumentItem
                key={document.id}
                document={document}
                onDelete={onDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200 space-y-2 shrink-0">
        {error && (
          <p
            role="alert"
            className="text-xs text-red-500 bg-red-50 border border-red-200 rounded px-2 py-1"
          >
            {error}
          </p>
        )}

        <UploadDocument
          onUpload={onUpload}
          disabled={uploadLimitReached}
          isUploading={isUploading}
        />

        {uploadLimitReached && (
          <p className="text-xs text-amber-600 text-center">
            Maximum of {maxSources} documents reached.
          </p>
        )}
      </div>
    </aside>
  );
}

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
    <aside>
      <div>
        <h2>Your Sources</h2>

        <span>
          {count} / {maxSources}
        </span>
      </div>

      <div>
        {isLoading && <p>Loading documents...</p>}

        {!isLoading && documents.length === 0 && (
          <p>No documents uploaded yet.</p>
        )}

        {!isLoading && documents.length > 0 && (
          <div>
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

      <div>
        {error && <p role="alert">{error}</p>}

        <UploadDocument
          onUpload={onUpload}
          disabled={uploadLimitReached}
          isUploading={isUploading}
        />

        {uploadLimitReached && (
          <p>
            Maximum of {maxSources} documents reached. Delete a document to add
            another.
          </p>
        )}
      </div>
    </aside>
  );
}

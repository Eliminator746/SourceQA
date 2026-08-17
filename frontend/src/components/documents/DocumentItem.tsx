import type { Document } from "../../types/document";

interface DocumentItemProps {
  document: Document;
  onDelete: (documentId: string) => Promise<void>;
}

export default function DocumentItem({
  document,
  onDelete,
}: DocumentItemProps) {
  const handleDelete = async () => {
    const confirmed = window.confirm(`Delete "${document.filename}"?`);

    if (!confirmed) {
      return;
    }

    await onDelete(document.id);
  };

  return (
    <div>
      <div>
        <span>📄</span>

        <div>
          <p>{document.filename}</p>

          <small>{document.file_type.toUpperCase()}</small>
        </div>
      </div>

      <button
        type="button"
        onClick={handleDelete}
        aria-label={`Delete ${document.filename}`}
      >
        🗑
      </button>
    </div>
  );
}

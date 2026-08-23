import type { Document } from "../../types/document";

interface DocumentItemProps {
  document: Document;
  onDelete: (documentId: string) => Promise<void>;
}

const STATUS_BADGE: Record<string, string> = {
  processing: "bg-amber-50 text-amber-600 border-amber-200",
  ready: "bg-green-50 text-green-600 border-green-200",
  failed: "bg-red-50 text-red-600 border-red-200",
};

const STATUS_LABEL: Record<string, string> = {
  processing: "⏳ Indexing…",
  ready: "✅ Ready",
  failed: "❌ Failed",
};

export default function DocumentItem({
  document,
  onDelete,
}: DocumentItemProps) {
  const handleDelete = async () => {
    const confirmed = window.confirm(`Delete "${document.filename}"?`);
    if (!confirmed) return;
    await onDelete(document.id);
  };

  const badgeClass =
    STATUS_BADGE[document.status] ?? "bg-gray-50 text-gray-500 border-gray-200";
  const statusLabel = STATUS_LABEL[document.status] ?? document.status;

  return (
    <div className="flex items-center gap-2 rounded-lg px-2 py-2 hover:bg-gray-50 group transition">
      <span className="text-lg shrink-0">📄</span>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-800 truncate">
          {document.filename}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="text-[10px] text-gray-400 uppercase font-mono">
            {document.file_type}
          </span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${badgeClass}`}
          >
            {statusLabel}
          </span>
        </div>
      </div>
      <button
        type="button"
        onClick={handleDelete}
        aria-label={`Delete ${document.filename}`}
        className="shrink-0 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition text-sm"
      >
        🗑
      </button>
    </div>
  );
}

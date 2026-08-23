import { useRef, useState } from "react";

interface UploadDocumentProps {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
  isUploading?: boolean;
}

const ALLOWED_FILE_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function UploadDocument({
  onUpload,
  disabled = false,
  isUploading = false,
}: UploadDocumentProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    setError(null);

    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setError("Only PDF, DOCX, and TXT files are supported.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must be 10 MB or less.");
      return;
    }

    try {
      await onUpload(file);
    } catch {
      // Error handled by useDocuments
    }
  };

  const openFilePicker = () => {
    if (disabled || isUploading) return;
    fileInputRef.current?.click();
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        onChange={handleFileChange}
        disabled={disabled || isUploading}
        hidden
      />

      <button
        type="button"
        onClick={openFilePicker}
        disabled={disabled || isUploading}
        className="w-full py-2 rounded-lg border-2 border-dashed border-gray-200 text-sm text-gray-500 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
      >
        {isUploading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Uploading…
          </span>
        ) : (
          "+ Add document"
        )}
      </button>

      {error && (
        <p role="alert" className="text-xs text-red-500 mt-1">
          {error}
        </p>
      )}
    </div>
  );
}

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

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

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

    // Reset the input so selecting the same file again
    // will trigger onChange.
    event.target.value = "";

    if (!file) {
      return;
    }

    setError(null);

    // ---------------------------------------------
    // Validate file type
    // ---------------------------------------------

    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      setError("Only PDF, DOCX, and TXT files are supported.");

      return;
    }

    // ---------------------------------------------
    // Validate file size
    // ---------------------------------------------

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must be 10 MB or less.");

      return;
    }

    try {
      await onUpload(file);
    } catch {
      // Error is already handled by useDocuments.
    }
  };

  const openFilePicker = () => {
    if (disabled || isUploading) {
      return;
    }

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
      >
        {isUploading ? "Uploading..." : "+ Add document"}
      </button>

      {error && <p role="alert">{error}</p>}
    </div>
  );
}

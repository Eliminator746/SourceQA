import { useState, type ChangeEvent } from "react";

interface QuestionInputProps {
  onAsk: (question: string) => Promise<boolean>;
  disabled?: boolean;
  isLoading?: boolean;
}

export default function QuestionInput({
  onAsk,
  disabled = false,
  isLoading = false,
}: QuestionInputProps) {
  const [question, setQuestion] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    setValidationError(null);

    if (!trimmedQuestion) {
      setValidationError("Please enter a question.");
      return;
    }

    if (disabled || isLoading) return;

    const success = await onAsk(trimmedQuestion);
    if (success) setQuestion("");
  };

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setQuestion(event.target.value);
    if (validationError) setValidationError(null);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  const isDisabled = disabled || isLoading;

  return (
    <div className="px-4 pb-4 pt-2 bg-white border-t border-gray-200 shrink-0">
      {validationError && (
        <p role="alert" className="text-xs text-red-500 mb-2">
          {validationError}
        </p>
      )}
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <div className="flex-1 relative">
          <textarea
            id="question"
            value={question}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={
              isDisabled && !isLoading
                ? "Upload a document to start asking questions…"
                : "Ask something about your documents… (Enter to send)"
            }
            rows={2}
            maxLength={2000}
            disabled={isDisabled}
            className="w-full resize-none rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition"
          />
          <span className="absolute bottom-2 right-3 text-[10px] text-gray-300 select-none">
            {question.length}/2000
          </span>
        </div>
        <button
          type="submit"
          disabled={isDisabled || !question.trim()}
          className="shrink-0 h-11 px-5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-2"
        >
          {isLoading ? (
            <>
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
              Searching your documents…
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
              Ask
            </>
          )}
        </button>
      </form>
    </div>
  );
}
